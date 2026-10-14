import { IconLock } from "../components/Icons";

const H2 = ({ children }: { children: React.ReactNode }) => (
  <h2 className="mb-2 mt-8 text-xl font-semibold text-ink">{children}</h2>
);

export default function Privacy() {
  return (
    <article className="card prose-lite mx-auto max-w-3xl p-6 text-ink-soft sm:p-10">
      <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-700">
        <IconLock className="h-6 w-6" />
      </span>
      <h1 className="text-3xl font-extrabold text-ink">Privacy and disclaimer</h1>
      <p className="mt-4">
        This is an independent assistance tool. It is not operated by, endorsed by, or affiliated
        with any government body. It does not submit applications and has no access to any
        government database. Results are preliminary and are not a decision about eligibility.
      </p>

      <H2>What we collect</H2>
      <ul className="list-disc space-y-2 pl-6">
        <li>
          Only the answers needed to match schemes (age, state, income, education, and disability
          details if you choose to give them). Disability questions can be skipped.
        </li>
        <li>No names, phone numbers, Aadhaar or UDID numbers, passwords, or document images.</li>
        <li>
          Your answers are kept in this browser tab&apos;s session storage and sent to our server
          only to compute results. They are not saved there.
        </li>
      </ul>

      <H2>The AI assistant</H2>
      <p>
        When you chat, your question and only the answers relevant to the schemes being discussed
        are sent to the language-model provider configured by the operator of this service.
        You can switch this off with &quot;Use my answers to personalise replies&quot;. Do not type
        personal identifiers into the chat.
      </p>

      <H2>Saved conversations and deletion</H2>
      <p>
        Conversations are not stored unless you tick &quot;Save this conversation&quot;. Saved
        conversations are deleted automatically after 30 days, and you can delete one immediately
        with &quot;Delete saved conversation&quot;. Clearing your browser session removes your
        answers.
      </p>

      <H2>Accuracy</H2>
      <p>
        Scheme rules change and some official sources could not be verified. Each scheme shows its
        verification status and when it was last checked. Always confirm eligibility, benefits and
        deadlines with the official source linked on the scheme.
      </p>
    </article>
  );
}
