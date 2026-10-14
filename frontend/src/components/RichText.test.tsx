import { render, screen } from "@testing-library/react";
import RichText from "./RichText";

describe("RichText", () => {
  it("renders bold and citation tags without showing markdown syntax", () => {
    const { container } = render(<p><RichText text="Rs **1,000 per month**[S1][E2] only." /></p>);
    expect(screen.getByText("1,000 per month").tagName).toBe("STRONG");
    expect(container.textContent).toBe("Rs 1,000 per monthS1E2 only.");
    expect(container.querySelectorAll("sup")).toHaveLength(2);
  });

  it("never turns model or document text into HTML", () => {
    const { container } = render(<p><RichText text={'<img src=x onerror="alert(1)"> **<b>x</b>**'} /></p>);
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("b")).toBeNull();
    expect(container.textContent).toContain("<img src=x");
  });

  it("leaves unmatched markers alone", () => {
    const { container } = render(<p><RichText text="2 ** 3 and [X9] and [S]" /></p>);
    expect(container.textContent).toBe("2 ** 3 and [X9] and [S]");
  });
});
