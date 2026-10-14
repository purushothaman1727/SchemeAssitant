import { EMPTY_FORM, toPayload } from "./profile";

describe("toPayload", () => {
  it("drops disability details unless the answer is yes", () => {
    const p = toPayload({
      ...EMPTY_FORM, disability_status: "no", disability_type: "visual",
      certificate_status: "udid", disability_percentage: 80,
    });
    expect(p.disability_type).toBeNull();
    expect(p.certificate_status).toBeNull();
    expect(p.disability_percentage).toBeNull();
  });

  it("keeps disability details when the answer is yes", () => {
    const p = toPayload({
      ...EMPTY_FORM, disability_status: "yes", disability_type: "locomotor",
      certificate_status: "udid", disability_percentage: "45",
    });
    expect(p.disability_percentage).toBe(45);
    expect(p.disability_type).toBe("locomotor");
  });

  it("maps blanks to null and tri-state answers to booleans", () => {
    const p = toPayload({ ...EMPTY_FORM, age: "", is_bpl: "yes", is_widow: "no", district: "  " });
    expect(p.age).toBeNull();
    expect(p.district).toBeNull();
    expect(p.is_bpl).toBe(true);
    expect(p.is_widow).toBe(false);
    expect(p.guardian_has_disability).toBeNull();
  });

  it("never sends consent flags or unknown keys to the API", () => {
    const keys = Object.keys(toPayload(EMPTY_FORM));
    expect(keys).not.toContain("consent_process");
    expect(keys).toHaveLength(20);
  });

  it("treats prefer-not-to-say as a distinct value, not as no", () => {
    expect(toPayload(EMPTY_FORM).disability_status).toBe("prefer_not_to_say");
  });
});
