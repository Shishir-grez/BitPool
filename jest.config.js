module.exports = {
    preset: "ts-jest", // Use ts-jest for TypeScript
    testEnvironment: "node", // Use Node.js environment
    testMatch: ["**/*.test.ts"], // Look for test files ending with .test.ts
    moduleFileExtensions: ["ts", "js"], // Support .ts and .js files
    transform: {
        "^.+\\.ts$": "ts-jest" // Transform .ts files with ts-jest
    },
    collectCoverage: true, // Enable coverage reporting
    coverageDirectory: "coverage", // Output coverage reports to the coverage/ directory
    coverageReporters: ["text", "lcov"] // Generate text and lcov reports
};