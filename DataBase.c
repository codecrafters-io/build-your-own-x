#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
// Structure for Input from KeyBoard
typedef struct
{
  char *buffer;
  size_t buffer_length; // un signed
  ssize_t input_length;
} InputBuffer;

// stuctute of enum type to represent "." cmds success and failure
typedef enum
{
  META_COMMAND_SUCCESS,
  META_COMMAND_UNRECOGNIZED_COMMAND
} MetaCommandresult;
// structure of enum type to represent query success and failure
typedef enum
{
  PREPARE_SUCCESS,
  PREPARE_UNRECOGNIZED_STATEMENT
} PreparedResult;
// structure of enum type to represent the query types
typedef enum
{
  STATEMENT_INSERT,
  STATEMENT_SELECT
} StatementType;

// structure of enum type to represent the query type
typedef struct
{
  StatementType type;
} Statement;

// freeing memory
void close_input_buffer(InputBuffer *input_buffer)
{
  free(input_buffer->buffer);
  free(input_buffer);
}

// function to to identify meta commands
MetaCommandresult do_Meta_Command(InputBuffer* input)
{
  if (strcmp(".exit", input->buffer) == 0)
  {
    close_input_buffer(input);
    exit(0);
  }
  else
  {
    return META_COMMAND_UNRECOGNIZED_COMMAND;
  }
}
// function to set statement type and return success or unknoum cmd
PreparedResult prepare_Statement(Statement *statement, InputBuffer* input)
{
  if (strncmp("insert", input->buffer, 6) == 0)
  {
    statement->type = STATEMENT_INSERT;
    return PREPARE_SUCCESS;
  }
  else if (strncmp("update", input->buffer, 6) == 0)
  {
    statement->type = STATEMENT_SELECT;
    return PREPARE_SUCCESS;
  }
  else
  {
    return PREPARE_UNRECOGNIZED_STATEMENT;
  }
}

// function which returns input_buffer with default values set like null,0,0.
InputBuffer *new_input_buffer()
{
  InputBuffer *input_buffer = malloc(sizeof(InputBuffer));
  input_buffer->buffer = NULL;
  input_buffer->buffer_length = 0;
  input_buffer->input_length = 0;

  return input_buffer;
}

// fuction to execute cmds
void execute_statement(Statement *statement)
{
  switch (statement->type)
  {
  case STATEMENT_INSERT:
    printf("Here we would write execution for insert.\n");
    break;
  case STATEMENT_SELECT:
    printf("Here we would write execution for update.\n");
    break;
  }
}
// function to print console
void print_prompt() { printf("db > "); }

// function to take input
void read_input(InputBuffer *input_buffer)
{
  ssize_t bytes_read =
      getline(&(input_buffer->buffer), &(input_buffer->buffer_length), stdin);

  if (bytes_read <= 0)
  {
    printf("Error reading input\n");
    exit(EXIT_FAILURE);
  }

  // Ignore trailing newline
  input_buffer->input_length = bytes_read - 1;
  input_buffer->buffer[bytes_read - 1] = 0;
}



// main function with while loop
int main(int argc, char *argv[])
{
  InputBuffer *input_buffer = new_input_buffer();
  while (true)
  {
    print_prompt();           // db >
    read_input(input_buffer); // reading input

    if (input_buffer->buffer[0] == '.')
    { // if user typed .exit
      switch (do_Meta_Command(input_buffer))
      {
      case (META_COMMAND_SUCCESS):
        continue;
      case (META_COMMAND_UNRECOGNIZED_COMMAND):
        printf("Unrecognized command.. %s\n", input_buffer->buffer);
        continue;
      }
    }
    Statement statement;
    switch (prepare_Statement(&statement,input_buffer))
    {
    case PREPARE_SUCCESS:
      break;
    case PREPARE_UNRECOGNIZED_STATEMENT:
      printf("Unrecognized command.. %s\n", input_buffer->buffer);
      continue;
    }
    execute_statement(&statement);
    printf("\nExecuted.\n");
  }
}