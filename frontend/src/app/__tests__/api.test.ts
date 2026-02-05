import { describe, it, expect } from "vitest"
import { api } from "../api"

describe("API Module", () => {
  describe("baseApi exports", () => {
    it("should export the main api object", () => {
      expect(api).toBeDefined()
      expect(api.reducerPath).toBe("api")
    })

    it("should have endpoints configured", () => {
      expect(api.endpoints).toBeDefined()
      expect(Object.keys(api.endpoints).length).toBeGreaterThan(0)
    })
  })

  describe("Investigation endpoints", () => {
    it("should have Investigation 2.0 endpoints", () => {
      expect(api.endpoints.launchInvestigation2).toBeDefined()
      expect(api.endpoints.getInvestigation2).toBeDefined()
    })
  })

  describe("Tiger endpoints", () => {
    it("should have tiger identification endpoints", () => {
      expect(api.endpoints.identifyTiger).toBeDefined()
      expect(api.endpoints.getTigers).toBeDefined()
    })
  })

  describe("Backward compatibility", () => {
    it("should maintain single api export", () => {
      const module = require("../api")
      expect(module.api).toBeDefined()
      expect(module.api).toBe(api)
    })
  })
})
