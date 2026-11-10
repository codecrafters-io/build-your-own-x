package main

import (
	"flag"
	"fmt"
)

func main() {
	name := flag.String("name", "friend", "name to greet")
	flag.Parse()

	fmt.Printf("Hello, %s! Welcome to build-your-own-x.\n", *name)
}
