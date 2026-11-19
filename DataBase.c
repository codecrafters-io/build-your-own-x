#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <stdint.h>
// Structure for Input from KeyBoard
typedef struct
{
  char *buffer;
  size_t buffer_length; // un signed
  ssize_t input_length;
} InputBuffer;
// execution representation
typedef enum
{
  EXECUTE_SUCCESS,
  EXECUTE_TABLE_FULL
} ExecuteResult;

// Row in the table
#define coloumn_username_size 32
#define column_email_size 255
typedef struct
{
  uint32_t id;
  char username[coloumn_username_size];
  char email[column_email_size];
} Row;
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
  PREPARE_UNRECOGNIZED_STATEMENT,
  PREPARE_SYNTAX_ERROR
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
  Row row_to_insert;
} Statement;

// fuction to return size of attributes of struct type
#define size_Of_Attribute(Struct, Attribute) sizeof(((Struct *)0)->Attribute)
// sizes of attributes
const uint32_t size_of_id = size_Of_Attribute(Row, id);
const uint32_t size_of_username = size_Of_Attribute(Row, username);
const uint32_t size_of_email = size_Of_Attribute(Row, email);
const uint32_t offset_id = 0;
const uint32_t offset_username = offset_id + size_of_id;
const uint32_t offset_email = offset_username + size_of_username;
const uint32_t Row_size = size_of_id + size_of_username + size_of_email;

// serialization and deserialization
void seriliaze_row(Row *source, void *dest)
{
  memcpy(dest + offset_id, &(source->id), size_of_id);
  memcpy(dest + offset_username, &(source->username), size_of_username);
  memcpy(dest + offset_email, &(source->email), size_of_email);
}

void deserialize_row(void *source, Row *dest)
{
  memcpy(&(dest->id), source + offset_id, size_of_id);
  memcpy(&(dest->username), source + offset_username, size_of_username);
  memcpy(&(dest->email), source + offset_email, size_of_email);
}
// freeing memory
void close_input_buffer(InputBuffer *input_buffer)
{
  free(input_buffer->buffer);
  free(input_buffer);
}
// Table consists of multiple pages init multiple rows
const uint32_t page_size = 4096;
#define table_max_pages 100
const uint32_t Rows_per_page = page_size / Row_size;
const uint32_t TABLE_MAX_ROWS = Rows_per_page * table_max_pages;

typedef struct
{
  uint32_t num_rows;
  void *pages[table_max_pages];
} Table;

void *row_slot(Table *table, uint32_t row_num)
{
  uint32_t page_num = row_num / Rows_per_page;
  void *page = table->pages[page_num];
  if (page == NULL)
  {
    page = table->pages[page_num] = malloc(page_size);
  }
  uint32_t row_offset = row_num % Rows_per_page;
  uint32_t byte_offset = row_offset * Row_size;
  return page + byte_offset;
}
// function to to identify meta commands
MetaCommandresult do_Meta_Command(InputBuffer *input)
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
// printing row
void print_row(Row *row)
{
  printf("(%d, %s, %s)\n", row->id, row->username, row->email);
}
// function to set statement type and return success or unknoum cmd
PreparedResult prepare_Statement(Statement *statement, InputBuffer *input)
{
  if (strncmp("insert", input->buffer, 6) == 0)
  {
    statement->type = STATEMENT_INSERT;
    int args = sscanf(input->buffer, "insert %d %s %s", &(statement->row_to_insert.id), &(statement->row_to_insert.username), &(statement->row_to_insert.email));
    if (args < 3)
    {
      return PREPARE_SYNTAX_ERROR;
    }
    return PREPARE_SUCCESS;
  }
  else if (strncmp("select", input->buffer, 6) == 0)
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
ExecuteResult execute_insert(Statement *statement, Table *table)
{
  if (table->num_rows >= table_max_pages)
  {
    return EXECUTE_TABLE_FULL;
  }
  Row *row_to_insert = &(statement->row_to_insert);
  seriliaze_row(row_to_insert, row_slot(table, table->num_rows));
  table->num_rows += 1;
  return EXECUTE_SUCCESS;
}
ExecuteResult execute_select(Statement *statement, Table *table)
{
  Row row;
  for (uint32_t i = 0; i < table->num_rows; i++)
  {
    deserialize_row(row_slot(table, i), &row);
    print_row(&row);
  }
  return EXECUTE_SUCCESS;
}
// fuction to execute cmds
ExecuteResult execute_statement(Statement *statement, Table *table)
{
  switch (statement->type)
  {
  case STATEMENT_INSERT:
    return execute_insert(statement, table);
  case STATEMENT_SELECT:
    return execute_select(statement, table);
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
Table *new_table()
{
  Table *table = (Table *)malloc(sizeof(Table));
  for (uint32_t i = 0; i < table_max_pages; i++)
  {
    table->pages[i] = NULL;
  }
  return table;
}
void free_table(Table *table)
{
  for (int i = 0; table->pages[i]; i++)
  {
    free(table->pages[i]);
  }
  free(table);
}

// main function with while loop
int main(int argc, char *argv[])
{
  InputBuffer *input_buffer = new_input_buffer();
  Table *table = new_table();
  while (true)
  {
    print_prompt();           // db >
    read_input(input_buffer); // reading input

    if (input_buffer->buffer[0] == '.')
    {
      switch (do_Meta_Command(input_buffer))
      {
      case (META_COMMAND_SUCCESS):
        continue;
      case (META_COMMAND_UNRECOGNIZED_COMMAND):
        printf("Unrecognized command '%s'\n", input_buffer->buffer);
        continue;
      }
    }

    Statement statement;
    switch (prepare_Statement(&statement, input_buffer))
    {
    case PREPARE_SUCCESS:
      break;
    case PREPARE_SYNTAX_ERROR:
      printf("Syntax error. Could not parse statement.\n");
      continue;
    case PREPARE_UNRECOGNIZED_STATEMENT:
      printf("Unrecognized command.. %s\n", input_buffer->buffer);
      continue;
    }
    switch (execute_statement(&statement, table))
    {
    case (EXECUTE_SUCCESS):
      printf("Executed.\n");
      break;
    case (EXECUTE_TABLE_FULL):
      printf("Error: Table full.\n");
      break;
    }
  }
}