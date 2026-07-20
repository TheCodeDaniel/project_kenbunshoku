# I Taught a Security Camera to Say "I Don't Know" — and It Got More Useful, Not Less

_Tags: #ai #computervision #buildinpublic #hackathon #philosophy_

---

Somewhere around day four of building a doorbell-camera AI for a hackathon,
I caught my own system lying to me. Not maliciously — it was just guessing,
the way all of us do when we don't want to say "I don't know" out loud. The
fix for that turned out to be more interesting than anything else in the
build, so this post is mostly about that, with some genuinely funny/painful
bug stories along the way.

## The problem nobody built a camera to solve

Every doorbell camera on the market answers one question: _was there
motion?_ That's the wrong question. The right question — the one a human
actually wants answered at 11pm when their phone buzzes — is _should I
care about this?_ Cameras don't answer that, so people train themselves to
swipe the notification away without looking. The alert becomes noise. The
one time it isn't noise, you've already stopped paying attention.

So the project — I called it **Kenbunshoku** (見聞色, roughly "the art of
perceiving," a term from certain martial traditions for reading a
situation before it becomes obvious) — tries to add one missing layer:
_context_. Not "something moved." Something closer to "a person in a
delivery uniform is standing at your door with a package," or "someone is
lingering by the entrance at an unusual hour without a clear reason to be
there."

The architecture, in one breath: a local YOLOv8n detector watches a camera
stream and only forwards frames that actually contain a person. Those
frames go to a cloud backend that calls Qwen-VL (Alibaba Cloud's
vision-language model) to reason about what's actually happening in the
image. A lightweight memory layer checks whether this is a recurring
pattern. A push notification goes to the homeowner's phone with the
reasoning attached, in plain language. That's the whole system. No part of
it ever acts on your behalf — no locks, no alarms, no calls to anyone. It
tells you things. You decide.

That last sentence is doing more work than it looks like, and I'll come
back to it.

Here it is actually running, filmed on my phone with zero production
values whatsoever — a real detection, a real Qwen-VL classification, a
real push notification landing on a real device:

https://youtu.be/6j4ZZhUeahY

(Judge the system, not the cinematography.)

## The lie I caught it telling

Early on, the classification prompt just asked Qwen-VL to look at a frame
and decide: is this person "familiar," "delivery-like," or "anomalous"? I
tested it against a deliberately ugly, blurry, low-detail image — barely a
silhouette — expecting either a refusal or an honest "unclear." Instead I
got:

> "familiar" — _"...suggesting they are a known individual."_

Read that again. The model had no reference photo of anyone who lives at
this house. It had never seen this "known individual" before in its
existence. It could not possibly know that. And yet it produced a
confident, specific, entirely fabricated claim of recognition — because I
had asked it a question shaped like an identity question, and it answered
in kind, filling the gap with plausible-sounding language instead of
admitting the gap existed.

This is, if you squint, the exact same failure mode as a person who
doesn't want to look uninformed in a meeting. The information isn't
there, but the _shape of a confident answer_ is easy to produce, and
confident-shaped answers get rewarded more often than "I don't know"
ones — right up until the moment they're wrong in a way that matters.

The fix wasn't a bigger model or a longer prompt lecture. It was
redefining what "familiar" was even allowed to mean:

> "familiar" means the visit _presents as_ expected and low-concern —
> calm demeanor, ordinary daytime approach, no unusual items — not that
> you recognize the person's identity. You have no reference photos.

And one more line that did almost all of the actual work:

> If the visual evidence doesn't clearly support "familiar" or
> "delivery-like," choose "anomalous" rather than guessing.

Same blurry test image, same model, new prompt:

> "anomalous" — _"The image is too blurry to determine any clear
> behavior, carried items, or context, making it impossible to classify
> as familiar or delivery-like."_

That's not a worse answer. It's a _categorically more honest_ one. The
model went from confabulating a memory it didn't have to correctly
reporting the limits of what it could see. For a home security system,
"I'm not sure, so I'm erring cautious" is strictly better than a
confident wrong guess in either direction — and it only took giving the
model permission to say so.

## Refusing to build the "creepier, more expensive" version

The natural next question, if you're chasing "familiar" as identity
recognition, is: why not just do real face matching? Store embeddings,
compare against known visitors, get an actual identity-confidence score
back.

I sat with that question for a while and landed on: no, deliberately,
permanently, not out of laziness but out of principle.

Here's the reasoning. A system that stores biometric-adjacent data about
everyone who walks up to your door is a fundamentally different kind of
object than one that doesn't — different risk if it leaks, different
ethical weight, different relationship to the people it observes (some of
whom never consented to being in _anyone's_ facial recognition database,
let alone a hackathon project's). And critically: it wasn't necessary. The
actual product need — "don't wake me up for the same delivery guy every
Tuesday" — is fully satisfied by a much cheaper, much more honest
mechanism: pattern-matching on _visits_, not identity.

The memory layer just asks: has this camera seen a similar classification,
on the same day of week, at a similar time, repeatedly, in the last two
weeks? If yes, that's a "recognized pattern" — still logged, but the push
notification gets quietly suppressed instead of buzzing your phone for the
fifth Tuesday in a row. If a genuinely unrecognized, anomalous visit
happens even in a pattern-matched slot, it still gets through — the system
never goes quiet on "anomalous," patterned or not.

This costs nothing extra. No embeddings, no vector database, no additional
model calls, no image storage beyond what's needed for the one live
classification. It's just a SQLite table and a modest SQL query. And it
never claims to know something it doesn't. "This time slot has a routine"
is a true, verifiable, honest claim. "I recognize this specific human
being" is not a claim this system is entitled to make, so I made sure it
never could.

Cheap and honest turned out to be the same design decision twice.

## Restraint as the actual feature

The system never takes autonomous action. Not "rarely" — never, as a hard
rule I refused to relax even when it would have been a more impressive
demo. No auto-locking doors on "anomalous," no auto-calls to anyone, no
control signal of any kind, ever. Just a notification with reasoning
attached, to a human, who decides.

It would be easy to read that as a limitation — "the AI could do more but
we held it back." I'd argue the opposite: the restraint _is_ the design.
A system that watches your front door and occasionally gets it wrong (all
of them do) is tolerable precisely because the cost of being wrong is "a
slightly annoying notification," not "the system did something to a real
door because a vision model was 73% confident." Keeping a human in the
loop isn't a feature you bolt on later. It's the thing that makes
everything upstream of it — including the confident-sounding mistakes —
survivable.

## The bugs that only existed once I stopped trusting the diff

Every single one of these passed a code review. All of them looked fine on
the page. None of them were fine.

- **An em dash crashed a push notification.** The alert title used a
  plain em dash for style. HTTP header values have to be ASCII/latin-1.
  The request didn't fail loudly in a way that pointed at the cause — it
  just threw a `UnicodeEncodeError` deep inside a networking library, the
  first time a real alert actually tried to fire. Nothing about the code
  _looked_ wrong.
- **A mobile OS silently ate all outbound network traffic.** The
  notification client connected to nothing, showed no error, gave no
  signal that anything was wrong — because macOS's App Sandbox was
  quietly blocking every request at the entitlement level, before it ever
  reached a socket. Android had the mirror-image problem: no `INTERNET`
  permission declared, same silent nothing. Static analysis had nothing
  to say about either one. Only running the actual app on actual hardware
  surfaced them.
- **The camera loop got stuck reprocessing the past.** Point the camera
  at your hand, then a pen, then your face — and the system kept
  reporting the pen. Not broken, exactly: `cv2.VideoCapture` buffers
  incoming frames faster than a multi-second classification round-trip
  can drain them, so the loop was dutifully working through a growing
  backlog of _old_ frames while the live scene moved on without it. The
  fix was a background thread that keeps only the newest frame and lets
  everything older get silently, deliberately discarded — the standard
  answer to this exact class of problem, but only obvious once you've
  watched it happen with your own hand in front of your own camera.
- **The system got slower the more careful it became.** A single request
  was quietly doing two sequential network calls before responding — one
  to the vision model, one to the push service — with no timeout set on
  either. Most of the time it was fine. Occasionally, both hops had a
  slow moment at once, blew past the timeout budget, and the system fell
  back to a generic "cloud unreachable" alert instead of the real
  classification it had actually computed a few seconds too late.

None of these are exotic. Every one of them is a well-known category of
bug with a well-known fix. What they have in common is that _reading the
code gave no signal anything was wrong._ The only way to find any of them
was to run the actual thing, on actual hardware, against an actual
network, and watch it fail in front of me.

## The recursive part

I built this with an AI pair programmer doing most of the typing. There's
an irony there I didn't fully appreciate until I was three days in:
I spent this entire project teaching one AI system to stop confidently
guessing and start admitting uncertainty — while collaborating, in real
time, with a _different_ AI system whose suggestions also needed
constant grounding against reality rather than being trusted on the
strength of how plausible they sounded. Code that compiles is not code
that works. A plan that reads well is not a plan that survives contact
with a real phone, a real Alibaba Cloud console, a real curl command
against a real server.

The throughline for the whole build, human-authored parts and
AI-authored parts alike, ended up being the same single sentence: _verify
against reality, not against your own confidence._ That sentence is the
entire fix for the "familiar" hallucination. It's the entire fix for
every bug in the list above. It's also, probably, decent advice for
anyone shipping anything, with or without a vision model attached.

---

_Kenbunshoku was built for the Global AI Hackathon Series with Qwen
Cloud, running on Alibaba Cloud ECS with Qwen-VL for visitor reasoning.
Camera-agnostic by design, human-in-the-loop by principle, and — as of
this week — a little more honest about what it doesn't know._
