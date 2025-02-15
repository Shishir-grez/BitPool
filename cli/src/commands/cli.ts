#!/usr/bin/env node

import readline from "readline";
import { program } from "commander";
import dotenv from "dotenv";

// Load environment variables
dotenv.config();

// Dynamically import chalk since it's ESM-only
const chalk = await import("chalk").then(mod => mod.default);

// Process direct commands first (e.g., `npm start register`)
program
  .name("bitpool")
  .description("CLI tool for distributed computing nodes")
  .version("1.0.0");

// Define commands
program
  .command("register")
  .description("Register a compute node")
  .action(() => {
    console.log(chalk.green("Registering a new compute node..."));
    process.exit(0);
  });

program
  .command("list")
  .description("List all compute nodes")
  .action(() => {
    console.log(chalk.cyan("Fetching all registered nodes..."));
    process.exit(0);
  });

// Parse CLI arguments
program.parse(process.argv);

// If no command is provided, start interactive mode
if (process.argv.length <= 2) {
  console.log(chalk.blue("🚀 Bitpool CLI Started. Type 'help' for commands.\n"));

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: chalk.green("bitpool> "),
  });

  rl.prompt();

  rl.on("line", async (line: string) => {
    const args = line.trim().split(" ");

    switch (args[0]) {
      case "help":
        console.log(chalk.yellow("Available commands:"));
        console.log(" - register : Register a compute node");
        console.log(" - list     : List all connected nodes");
        console.log(" - exit     : Exit the CLI");
        break;

      case "register":
        console.log(chalk.green("Registering a new compute node..."));
        break;

      case "list":
        console.log(chalk.cyan("Fetching all registered nodes..."));
        break;

      case "exit":
        console.log(chalk.red("Exiting Bitpool CLI..."));
        process.exit(0);

      default:
        console.log(chalk.red("Unknown command. Type 'help' for a list of commands."));
    }

    rl.prompt();
  });
}
