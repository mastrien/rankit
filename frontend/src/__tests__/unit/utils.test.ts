import { describe, expect, it } from "vitest";
import { cn } from "@/lib/utils";

describe("cn utility", () => {
  it("merges conditional classes and resolves tailwind conflicts", () => {
    const result = cn("px-2 py-1", false && "hidden", "px-4");
    expect(result).toBe("py-1 px-4");
  });
});
