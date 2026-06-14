# Tutorial — Escribe un Shell en C

*Stephen Brennan • 16 de enero de 2015*  
*Traducción al español: [orellanaignaciod-stack](https://github.com/orellanaignaciod-stack) — bajo licencia [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.es)*  
*Artículo original (en inglés): [brennan.io/2015/01/16/write-a-shell-in-c](https://brennan.io/2015/01/16/write-a-shell-in-c/)*

---

Es fácil sentir que uno "no es un programador de verdad". Hay programas que todo el mundo usa, y es tentador idealizar a quienes los crearon. Aunque desarrollar proyectos de software grandes no es sencillo, muchas veces la idea central de ese software es bastante simple. Implementarlo por tu cuenta es una forma entretenida de demostrar —y demostrarte— que tienes lo necesario para ser un programador de verdad.

Este es un recorrido por cómo escribí mi propio shell Unix simplificado en C, con la esperanza de que otros sientan lo mismo.

El código del shell descrito aquí, llamado `lsh`, está disponible en [GitHub](https://github.com/brenns10/lsh).

> **Atención estudiantes universitarios:** Muchas clases tienen tareas que piden escribir un shell, y algunos docentes conocen este tutorial y su código. Si eres estudiante en una de esas clases, no deberías copiar (ni copiar y modificar) este código sin permiso.

---

## El ciclo de vida básico de un shell

Miremos un shell desde arriba hacia abajo. Un shell hace tres cosas principales durante su vida:

- **Inicializar**: En este paso, un shell típico leería y ejecutaría sus archivos de configuración, que cambian aspectos de su comportamiento.
- **Interpretar**: Luego, el shell lee comandos desde `stdin` (que puede ser interactivo o un archivo) y los ejecuta.
- **Terminar**: Después de ejecutar sus comandos, el shell ejecuta cualquier comando de cierre, libera memoria y termina.

Estos pasos son tan generales que podrían aplicar a muchos programas, pero los usaremos como base para nuestro shell. El nuestro será tan simple que no tendrá archivos de configuración ni comandos de cierre. Solo llamaremos a la función de bucle y terminaremos. Pero en términos de arquitectura, es importante recordar que la vida de un programa es más que un simple bucle.

```c
int main(int argc, char **argv)
{
  // Cargar archivos de configuración, si los hay.

  // Ejecutar el bucle de comandos.
  lsh_loop();

  // Realizar tareas de cierre/limpieza.

  return EXIT_SUCCESS;
}
```

Aquí simplemente ideé una función, `lsh_loop()`, que hará un bucle interpretando comandos. Veremos su implementación a continuación.

---

## El bucle básico del shell

Ya definimos cómo debe arrancar el programa. Ahora, la lógica principal: ¿qué hace el shell en su bucle? Una forma simple de manejar comandos es con tres pasos:

- **Leer**: Leer el comando desde la entrada estándar.
- **Parsear**: Separar la cadena de texto del comando en programa y argumentos.
- **Ejecutar**: Correr el comando parseado.

Así se traducen esas ideas en código para `lsh_loop()`:

```c
void lsh_loop(void)
{
  char *line;
  char **args;
  int status;

  do {
    printf("> ");
    line = lsh_read_line();
    args = lsh_split_line(line);
    status = lsh_execute(args);

    free(line);
    free(args);
  } while (status);
}
```

Las primeras líneas son solo declaraciones. El bucle `do-while` es más conveniente para chequear la variable `status`, porque se ejecuta al menos una vez antes de verificar su valor. Dentro del bucle: imprimimos el prompt, llamamos a una función para leer una línea, otra para dividirla en argumentos, y ejecutamos esos argumentos. Al final, liberamos la memoria de `line` y `args`. La variable `status` que retorna `lsh_execute()` determina cuándo salir.

---

## Leer una línea

Leer una línea desde `stdin` suena simple, pero en C puede ser un dolor de cabeza. El problema es que no sabes de antemano cuánto texto va a escribir el usuario. No puedes simplemente reservar un bloque de memoria fijo y esperar que no lo exceda. En cambio, debes empezar con un bloque y, si el usuario lo supera, reasignar más espacio. Esta es una estrategia común en C:

```c
#define LSH_RL_BUFSIZE 1024
char *lsh_read_line(void)
{
  int bufsize = LSH_RL_BUFSIZE;
  int position = 0;
  char *buffer = malloc(sizeof(char) * bufsize);
  int c;

  if (!buffer) {
    fprintf(stderr, "lsh: error de asignación de memoria\n");
    exit(EXIT_FAILURE);
  }

  while (1) {
    // Leer un carácter
    c = getchar();

    // Si llegamos a EOF, reemplazarlo con un carácter nulo y retornar.
    if (c == EOF || c == '\n') {
      buffer[position] = '\0';
      return buffer;
    } else {
      buffer[position] = c;
    }
    position++;

    // Si excedimos el buffer, reasignar.
    if (position >= bufsize) {
      bufsize += LSH_RL_BUFSIZE;
      buffer = realloc(buffer, bufsize);
      if (!buffer) {
        fprintf(stderr, "lsh: error de asignación de memoria\n");
        exit(EXIT_FAILURE);
      }
    }
  }
}
```

> **¿Por qué `int` y no `char` para leer el carácter?** Porque `EOF` es un entero, no un carácter. Si usas `char`, no podrás detectarlo correctamente. ¡Es un error clásico en C!

El núcleo de la función está en el bucle `while(1)`. Leemos un carácter: si es salto de línea o `EOF`, terminamos la cadena con `\0` y la retornamos. De lo contrario, lo agregamos al buffer y verificamos si necesitamos expandirlo.

> **Nota:** Las versiones modernas de la biblioteca C incluyen `getline()` en `stdio.h`, que hace casi todo este trabajo. Es una buena función para conocer, pero te recomendamos aprender este enfoque manual primero — te enseña cómo funciona la gestión dinámica de memoria en C.

---

## Parsear la línea

Con `lsh_read_line()` implementada, tenemos la línea de entrada. Ahora hay que parsearla: dividirla en una lista de argumentos.

Haremos una simplificación importante: no soportaremos comillas ni escapes con backslash. Solo usaremos espacios en blanco para separar argumentos. Eso significa que usaremos `strtok` para tokenizar la cadena:

```c
#define LSH_TOK_BUFSIZE 64
#define LSH_TOK_DELIM " \t\r\n\a"
char **lsh_split_line(char *line)
{
  int bufsize = LSH_TOK_BUFSIZE, position = 0;
  char **tokens = malloc(bufsize * sizeof(char*));
  char *token;

  if (!tokens) {
    fprintf(stderr, "lsh: error de asignación de memoria\n");
    exit(EXIT_FAILURE);
  }

  token = strtok(line, LSH_TOK_DELIM);
  while (token != NULL) {
    tokens[position] = token;
    position++;

    if (position >= bufsize) {
      bufsize += LSH_TOK_BUFSIZE;
      tokens = realloc(tokens, bufsize * sizeof(char*));
      if (!tokens) {
        fprintf(stderr, "lsh: error de asignación de memoria\n");
        exit(EXIT_FAILURE);
      }
    }

    token = strtok(NULL, LSH_TOK_DELIM);
  }
  tokens[position] = NULL;
  return tokens;
}
```

La lógica es similar a `lsh_read_line()`: buffer dinámico que se expande según se necesita. La diferencia es que ahora el buffer contiene punteros a cadenas (tokens), no caracteres.

`strtok()` retorna punteros a dentro de la cadena original, colocando bytes `\0` al final de cada token. Guardamos cada puntero en nuestro array, hasta que `strtok` no retorna más tokens, momento en que terminamos el array con `NULL`.

---

## Cómo los shells inician procesos

Ahora llegamos al corazón de lo que hace un shell: iniciar procesos. Para escribir un shell, necesitas entender exactamente cómo funcionan los procesos en Unix.

Solo hay dos formas de iniciar procesos en Unix:

**1. Ser Init.**  
Cuando un sistema Unix arranca, el kernel carga y ejecuta un único proceso: `Init`. Este proceso vive todo el tiempo que la computadora está encendida y administra el arranque del resto.

**2. Usar `fork()`.**  
Cuando se llama a `fork()`, el sistema operativo crea un duplicado del proceso actual y los pone a ambos a correr. El proceso original es el "padre" y el nuevo es el "hijo". `fork()` retorna `0` al hijo y el PID (identificador de proceso) del hijo al padre.

Pero normalmente no quieres duplicar el mismo programa — quieres ejecutar uno diferente. Para eso existe `exec()`: reemplaza el programa en ejecución por uno nuevo. El proceso nunca retorna de una llamada a `exec()` (a menos que haya un error).

Con `fork()` + `exec()` tenemos los bloques fundamentales:
1. El proceso padre hace `fork()` → se crean dos copias.
2. El hijo llama a `exec()` → se convierte en el nuevo programa.
3. El padre llama a `wait()` → espera a que el hijo termine.

Con ese contexto, este código tiene sentido:

```c
int lsh_launch(char **args)
{
  pid_t pid, wpid;
  int status;

  pid = fork();
  if (pid == 0) {
    // Proceso hijo
    if (execvp(args[0], args) == -1) {
      perror("lsh");
    }
    exit(EXIT_FAILURE);
  } else if (pid < 0) {
    // Error al hacer fork
    perror("lsh");
  } else {
    // Proceso padre
    do {
      wpid = waitpid(pid, &status, WUNTRACED);
    } while (!WIFEXITED(status) && !WIFSIGNALED(status));
  }

  return 1;
}
```

Después de `fork()`, tenemos dos procesos corriendo simultáneamente. El hijo entra al primer `if` (donde `pid == 0`) y llama a `execvp()`:

- La `v` significa que los argumentos vienen en un array (vector).
- La `p` significa que el sistema buscará el programa en el `PATH`, no hace falta la ruta completa.

Si `exec` retorna, hubo un error — lo reportamos y salimos. El padre, en cambio, usa `waitpid()` para esperar a que el hijo termine (ya sea normalmente o por una señal).

---

## Comandos built-in del shell

Habrás notado que `lsh_loop()` llama a `lsh_execute()`, pero arriba implementamos `lsh_launch()`. ¡Intencional!

La mayoría de los comandos son programas externos, pero algunos deben estar integrados directamente en el shell. El motivo es simple: el directorio actual es una propiedad del proceso. Si `cd` fuera un programa externo, solo cambiaría su propio directorio y terminaría — el shell padre no se vería afectado. Por eso `cd` debe ser un comando interno del shell.

Lo mismo con `exit`: un programa llamado `exit` no podría cerrar el shell que lo invocó.

Aquí están los built-ins que implementaremos (`cd`, `help`, `exit`):

```c
/*
  Declaraciones de las funciones built-in:
*/
int lsh_cd(char **args);
int lsh_help(char **args);
int lsh_exit(char **args);

/*
  Lista de nombres de comandos built-in y sus funciones correspondientes.
*/
char *builtin_str[] = {
  "cd",
  "help",
  "exit"
};

int (*builtin_func[]) (char **) = {
  &lsh_cd,
  &lsh_help,
  &lsh_exit
};

int lsh_num_builtins() {
  return sizeof(builtin_str) / sizeof(char *);
}

/*
  Implementaciones de los built-ins.
*/
int lsh_cd(char **args)
{
  if (args[1] == NULL) {
    fprintf(stderr, "lsh: se esperaba un argumento para \"cd\"\n");
  } else {
    if (chdir(args[1]) != 0) {
      perror("lsh");
    }
  }
  return 1;
}

int lsh_help(char **args)
{
  int i;
  printf("LSH de Stephen Brennan\n");
  printf("Escribe el nombre de un programa y sus argumentos, luego presiona Enter.\n");
  printf("Los siguientes son comandos internos:\n");

  for (i = 0; i < lsh_num_builtins(); i++) {
    printf("  %s\n", builtin_str[i]);
  }

  printf("Usa el comando man para información sobre otros programas.\n");
  return 1;
}

int lsh_exit(char **args)
{
  return 0;
}
```

> **¿Qué es un puntero a función?** `builtin_func` es un array de punteros a funciones. Cada elemento apunta a una de las funciones built-in. Esto permite agregar nuevos comandos en el futuro modificando solo los arrays, sin tocar la lógica central. Es normal confundirse con la sintaxis — hasta el autor confiesa que aún la busca en Google después de 6 años.

---

## Uniendo built-ins y procesos

La pieza final del rompecabezas: `lsh_execute()`, que decide si correr un built-in o lanzar un proceso externo:

```c
int lsh_execute(char **args)
{
  int i;

  if (args[0] == NULL) {
    // Se ingresó un comando vacío.
    return 1;
  }

  for (i = 0; i < lsh_num_builtins(); i++) {
    if (strcmp(args[0], builtin_str[i]) == 0) {
      return (*builtin_func[i])(args);
    }
  }

  return lsh_launch(args);
}
```

Simple: si el comando coincide con un built-in, lo ejecuta. Si no, llama a `lsh_launch()`. También manejamos el caso de un comando vacío (el usuario solo presionó Enter).

---

## Juntando todo

Eso es todo el código del shell. Para probarlo en Linux:

1. Copia todos los fragmentos en un archivo `main.c`.
2. Incluye los siguientes headers:

```c
#include <sys/wait.h>   // waitpid() y macros asociadas
#include <unistd.h>     // chdir(), fork(), exec(), pid_t
#include <stdlib.h>     // malloc(), realloc(), free(), exit(), execvp()
#include <stdio.h>      // fprintf(), printf(), stderr, getchar(), perror()
#include <string.h>     // strcmp(), strtok()
```

3. Compila y ejecuta:

```bash
gcc -o main main.c
./main
```

También puedes obtener el código completo en el [repositorio de GitHub de lsh](https://github.com/brenns10/lsh).

---

## Cierre

Si te preguntás cómo saber qué llamadas al sistema usar, la respuesta es simple: **las páginas del manual** (`man 3p`). Ahí hay documentación exhaustiva de cada llamada al sistema. Si no sabes por dónde empezar, la [Especificación POSIX](http://pubs.opengroup.org/onlinepubs/9699919799/), Sección 13 ("Headers"), lista todo lo que cada header define.

Nuestro shell tiene varias limitaciones notables que podés explorar como ejercicio:

- Solo separa argumentos por espacios — sin comillas ni escapes.
- Sin pipes (`|`) ni redirección (`>`, `<`).
- Pocos built-ins.
- Sin globbing (`*.c`, `~/`).

Implementar cualquiera de estas cosas es muy interesante. ¡Anímate a intentarlo!

---

*Tutorial original de Stephen Brennan, publicado el 16 de enero de 2015 en [brennan.io](https://brennan.io/2015/01/16/write-a-shell-in-c/). Traducido y adaptado al español bajo los términos de la licencia [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/deed.es).*
