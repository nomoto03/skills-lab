import test from "node:test";
import assert from "node:assert/strict";
import { add } from "../src/add.mjs";

test("add", () => {
  assert.equal(add(1, 2), 3);
});
