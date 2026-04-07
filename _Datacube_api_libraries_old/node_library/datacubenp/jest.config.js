module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  roots: ["./tests"],
  transform: {
    "^.+\\.ts$": "ts-jest",
  },
};
