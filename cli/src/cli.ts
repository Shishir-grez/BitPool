import readline from "readline";
import { program } from "commander";
import dotenv from "dotenv";
import chalk from "chalk";

dotenv.config();

program
  .name("bitpool")
  .description("CLI tool for distributed computing nodes")
  .version("1.0.0");

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

// Check if a command was provided
const args = process.argv.slice(2);
if (args.length > 0) {
  program.parse(process.argv); // Run commander for script-like execution
} else {
  // No command provided → Enter interactive mode
  console.log(chalk.blue("Bitpool CLI Started. Type 'help' for commands.\n"));

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
