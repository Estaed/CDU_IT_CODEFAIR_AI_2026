# Research: how real dispatch consoles, housing repair triage and triage queues actually work

Prepared 2026-09-14. Every source was checked **2026-09-14**. Publication dates are given where a
page carries one; vendor help pages mostly do not and are marked `undated`. Research only: it
records what sources show and suggests, and decides nothing.

---

## 1. Dispatcher / coordinator consoles

### 1.1 Salesforce Field Service — Dispatcher Console

**Two regions: appointment list left, Gantt right. The map is a tab *inside* the Gantt.**
"The dispatcher console displays service appointments listed on the left and a Gantt chart
displayed on the right." The Gantt "contains the resource list, the schedule view" and displays
"appointments, absences, breaks, travel times, and service crew assignments". The map is reached
"by clicking **Map** in the Gantt": embedded Google traffic map with service territory polygons.
*Salesforce Help, "…Dispatcher Console Appointment List" and "…Dispatcher Console Gantt" (undated);
Trailhead, "Explore the Dispatcher Console" (undated).*
→ Fair Turn: list + map + selected-job pane is the recognised shape; the map is a *view onto the
list*, never a separate page.

**Priority shows as a header KPI bar and a jeopardy filter, not a per-row badge; colour is
configured, not fixed.** The **KPI bar** (top right of the Gantt) shows "total scheduled time,
average travel time per appointment, and the number of appointments that are **in jeopardy**";
dispatchers "can filter appointments to see the ones in jeopardy" — "appointments that are in
danger of missing their due dates". **Color-Code the Gantt** builds a palette from a service
appointment field, e.g. "a custom color spectrum based on the proximity of the due date". Other
named controls: **Policy selector** ("Choose the policy Field Service uses to schedule
appointments"), **Territories icon**, **Settings icon**, **Filter by Territory**. *As above.*
→ Fair Turn: a header strip of counts (in capacity / backlog / needs a human / worst days waited)
is the idiom; colour should encode *time against the promise*, not raw severity.

**"Schedule", "Dispatch" and "Optimize" are three separate verbs; emergency assignment is
distance-ranked and ends in an explicit confirm.** Bulk actions on selected appointments:
"schedule, dispatch, flag, unflag, or optimize". Named Gantt actions: **Schedule**, **Dispatch**,
**Optimize**, **Get Candidates**. In the emergency walkthrough the dispatcher opens the work order,
uses the **Emergency** tab, and **Emergency Dispatch** "displays the closest available mobile
workers who can help" with travel in plain words ("21 minutes away"); then **Dispatch**, then
**Confirm and Dispatch**. *Trailhead, "Handling Unexpected Situations" (undated).*
→ Fair Turn: daily sign-off is the analogue of **Dispatch** — a deliberate commitment separate
from ordering the list. Two-step confirm is normal, not friction.

**Overriding produces a visible, named defect rather than a silent change.** After an emergency
reassignment "there's a **rule violation** on the Gantt" because a worker was pulled off a
scheduled job; **Check Rule Violations** surfaces breaches with indicators on the timeline.
Rescheduling is right-click → **Reschedule**. *Same source.*
→ Fair Turn: when a coordinator overrides, name the consequence (who got displaced) on the same
screen. Closest real-world idiom for the equity trade-off.

### 1.2 ServiceNow Field Service Management — Dispatcher Workspace

**Three coordinated regions — task panel, dispatch map, schedule — plus a separate Dispatcher
Dashboard for the day's numbers.** "Dispatcher Workspace provides a configurable screen to view
unassigned tasks, technician schedules and maps." The **task panel** supports search and filter;
**task cards** and **agent cards** are both configurable. The **Dispatcher Dashboard** shows
"Statistics on critical pending dispatch tasks and **SLAs breached**" and technicians "behind the
schedule". *ServiceNow Docs, "Using Dispatcher Workspace"; product page (undated).*
→ Fair Turn: a card, not a table row, is the unit; a separate small dashboard of breach counts is
a recognised surface (Evidence lab).

**Selecting a map pin opens a contextual side panel — map and record pane are one interaction.**
"Unique task pins are displayed based on the state of the work order task"; pins cluster, and
"Select the map cluster to zoom the map to show the map markers of work order tasks and agents",
with cluster labels configurable to "show the total count of tasks and agents". Selecting a pin
opens a "**contextual side panel**" with "detailed scheduling and task or agent record
information". Hard limit: "The map can load at most 2000 records from the task panel and the
scheduler." *ServiceNow Docs, "Viewing agents and tasks in the Dispatcher Workspace map" (Zurich).*
→ Fair Turn: list ↔ map ↔ pane must be one selection — exactly the Task 22 design. Second
independent source for it.

**The "suggestion" is a ranking against named, inspectable criteria; the dispatcher still
assigns.** The workspace schedules "based on technician skills, parts, distance, recommendations,
and access hours". **Rank Resources** exposes **Default**, **Distance**, **Skills**, **Parts**,
**Auto Assign Rules**. Resource settings show "**Available Parts**", "**Matching Skills**",
"**Distance to Task**"; event settings "**Show travel time indicator**" / "**Show travel home time
indicator**"; task settings "**Notify me of new tasks before adding them to the list**".
*ServiceNow Docs, "Enable Dispatcher Workspace settings" (Zurich, undated); ServiceNow Community
thread on Rank Resources modes — **weaker evidence**, corroboration only.* **Contradiction:** the
product page advertises "Intelligent Task Recommendation" and "Dynamic Scheduling", but the
settings page carries no setting for ranking, recommendations, auto-assignment or a required
justification. **TBD:** whether ServiceNow ever forces a justification on override — none found.
→ Fair Turn: naming the ranking mode ("ranked by distance") is how real tools make a suggestion
legible. No vendor requires a reason — Fair Turn's mandatory reason is a *deliberate departure*.

### 1.3 Microsoft Dynamics 365 Field Service — schedule board

Best-documented of the five, and the only pages carrying explicit dates.

**Three regions — actions area, resource list, requirement pane — with view type switchable over
the same data.** Labelled regions: "1 Actions area, 2 Resource list, 3 Requirement pane". **View
type**: "Choose **Gantt** (bar chart showing activities over time), **List** (expandable resource
list with time granularity), or **Map** (large format map of resources, requirements, and routes
for a single day)." **Time scale** switches hourly / daily / weekly / monthly. The **Requirement
pane** "shows unscheduled requirements"; select one and select **Find availability** to launch the
schedule assistant, "which lists available and matching resources". *Microsoft Learn, "Use the
schedule board in Field Service", `ms.date: 2026-09-10`, updated 2026-09-11.*
→ Fair Turn: "same jobs, different view" is the mental model. Ranked list and map are two views of
one day — explicitly linked, never divergent.

**Colour meaning is published in a Legend, not guessed.** "Select **…** > **Legend** to view color
codes and icons for **status, priority, timeline, and travel time**." Availability uses a second
encoding: "available (colored) and unavailable (grayed out) time slots". A **Details panel** icon
shows "more details about the selected booking, resource, or requirement". *Same source.*
→ Fair Turn: ship a legend. Those four encodings are nearly Fair Turn's factor set, and a legend
turns a colour into an argument.

**Optimisation is offered at two explicitly different strengths, and the goal itself is a
user-visible setting.** "Select **Suggest resources (Preview)** to get suggestions from Resource
Scheduling Optimization about which resources to book. Select **Book resources (Preview)** to let
the system find the optimal resources and book directly." Single-resource re-optimisation is
right-click → **Optimize schedule**, recommended "after a resource's planned schedule changes due
to cancellations or emergency work". Crucially: "The default optimization goal is the default for
optimization requests. You can **change the optimization goal for each schedule board**."
*Same source; Microsoft Learn, "Overview of Resource Scheduling Optimization".*
→ Fair Turn: **"optimization goal" is a first-class, per-board, user-visible setting in a shipping
enterprise product** — the strongest external precedent for λ being a control, not a constant.

**Manual override is rich, and the docs are explicit that it changes the numbers in a way users
find surprising.** Drag-and-drop moves a booking between time slots or resource rows. Right-click
gives **Move to** (reassign to any resource, with a filter toggle from "**Resources on this tab**"
to "**All resources**", then **Update**), **Move by** ("move selected bookings forward or backward
by a set offset (for example, move three selected bookings back by two days)") and **Reassign to**.
A published table contrasts drag-and-drop with Move To on end date, travel time and resource scope.
Important callout: "When you use **Move To** or **Reassign to** …, the system recalculates travel
time from the new start point. This shifts the booking slot forward compared to the original
booking. This is expected behavior." *Microsoft Learn, "Drag and drop to schedule on the schedule
board", `ms.date: 2026-09-10`, updated 2026-09-11.*
→ Fair Turn: after an override, recompute and *show* the knock-on. Microsoft documents it because
users were surprised; Fair Turn can display it instead.

**The map is an input to scheduling, not a picture.** "On the map view, you can drag an unscheduled
requirement pin from the map to the resource timeline and schedule it to that resource… useful when
you want to quickly identify areas with unscheduled jobs and schedule them to the nearest
resources." *Same source.*
→ Fair Turn: geographic clustering *is* the efficiency pull that disadvantages remote communities.
A map that makes clustering attractive is the bias the tool counter-weights — say so in the report.

### 1.4 IBM Maximo / Maximo Scheduler

**Work is planned weeks ahead in a Gantt; "dispatch" is the separate, reactive act of reassigning
when the plan breaks.** "You dispatch work to assign resources, such as labor resources or assets,
to work orders." Work "is planned several weeks ahead of time in the Graphical Scheduling
application by coordinating new and unassigned work orders with the available resources, which can
be individual labor resources or crews and their tools." The topic frames itself entirely around
unplanned events. *IBM Docs, "Dispatching work in Graphical Assignment application" (undated).*
→ Fair Turn: the coordinator's morning is *re-planning*, not planning from zero. Yesterday's
unfinished backlog arriving into today is the realistic starting state.

**Assignment is drag-and-drop onto resource slots, with an automatic path and a manual dialog as
alternatives.** Graphical Assignment "gives supervisors visibility of their work, and visibility of
labor people and crews, allowing supervisors to drag and drop work onto resource slots to create
assignments". In "Planning and Scheduling > Graphical Assignment > **Work List**", work orders "can
be automatically assigned to an available resource, or a dialog with available resources appears
for manual selection before clicking the **Assign** button".
*IBM Support, "Dynamic Scheduling on Maximo Scheduler 7.5.2" (older release — **weaker evidence**);
IBM Training MAX4345G (undated).* **TBD:** no current IBM page found enumerating Graphical
Assignment's screen regions, priority columns or colours.
→ Fair Turn: "auto-assign, or show me the candidates and let me pick" is the same two-strength
pattern Microsoft ships. Fair Turn sits on the second setting by design.

### 1.5 Australian SMB tools

**ServiceM8 (AU) — one Dispatch Board with a map, *queues* as named holding pens, and an "Action
Required" list that is the real triage inbox.** "The Dispatch Board is the central hub for managing
your team and jobs in real time… you can see all your jobs on the map." Staff show on the map
"whenever they are Clocked On", not "while they are Clocked Off or On Break". Status dots: "**Blue
Dot** – job is scheduled to a staff member and they have not yet opened it (i.e. Unread). **Red
Dot** - staff member to review this job because it has not been completed following a scheduled
appointment. **Yellow Dot** – job is in a queue, or has expired from a queue." Queues are "virtual
folders that let you manage jobs on hold - without losing sight of them"; defaults **Parts on
Order**, **Pending Quotes**, **Workshop**; dragging a job into a queue column assigns "The default
**expiry date** set for that queue". A job enters **Action Required** when "It has no future
booking, or was booked to a team member in the past and hasn't been managed since", "It has expired
from a Queue without further action", or "It has an unanswered email or SMS from a client"; you
clear it by rescheduling, queueing, setting status Completed/Unsuccessful, or replying.
*ServiceM8 Help Centre, "Dispatch Board - Overview", "Queues - overview", "Using Action Required"
(undated).*
→ Fair Turn: **queues with expiry dates** are the best real answer to "a deferred job must not
vanish". A deprioritised remote job should carry a *date it comes back*, not just a lower rank.

**Simpro (AU) — colour by status, legend on the page, two colour channels per card.** "Schedules
are colour-coded by their status, unless otherwise defined in schedule defaults, with a legend at
the bottom of the page for quick colour code reference." Day/week/month with drag-and-drop. In
Simpro Mobile "the coloured status bar … matches the colour of the job status in Simpro Premium,
and the coloured circle around matches the colour of the current mobile status." *Simpro Help
Guide, "About Schedules", "How to Set Up Statuses" (undated).*
→ Fair Turn: two colour channels on one card (urgency band + "needs a human" ring) has precedent,
as does a legend at the bottom of the board.

**AroFlo (AU) — the same schedule as Timeline, Calendar or Map.** "AroFlo Field shows you your
scheduled events (tasks, overheads, ad-hoc events) in either a **Timeline**, **Calendar**, or
**Map** format"; the Schedule Map view "uses Google Maps to display tasks, quotes, and periodic
tasks that have been scheduled to you". *AroFlo Help, "Map View", "Schedules - Overview".*
→ Fair Turn: third confirmation that list/timeline and map are views of one schedule.

---

## 2. Public housing repair triage as tenants actually see it

### 2.1 Northern Territory — the primary source, and the equity gap is in it

**NT publishes three response classes, and two carry an explicitly longer remote clock. The
inequity Fair Turn models is stated in the government's own fact sheet.** Verbatim: "**Immediate
maintenance** – response time within 4 hours. **Urgent maintenance** – response time is within 2
business days. **Remote housing response time is within 5 business days.** **Routine maintenance**
– response time is within ten (10) business days. **Remote housing response time is within 25
business days.**" Also: "In remote areas, Remote Housing Maintenance Officers will step in to
assess and make safe if a contractor isn't available." What-next wording: "The Department will
organise a contractor to fix the problem. The contractor will then contact you to organise a
suitable time to come to your home." Trigger: "You should report any maintenance issue that is
dangerous or unhealthy."
*NT Dept of Housing, Local Government and Community Development, Fact sheet FS17 "Repairs and
maintenance", edition **10/25** (October 2025); local frozen copy
`data/raw/nt_fs17_repairs_and_maintenance_2025-10.pdf`, read 2026-09-14. The tfhc.nt.gov.au URL
returned **HTTP 403** on 2026-09-14; the local copy is the evidence.* Second, independent NT
source: "Routine maintenance has a response time of within ten (10) business days"; "things that
are dangerous will be repaired first". *nt.gov.au, "Repairs and maintenance of your public housing
home" (undated).*
→ Fair Turn: use **Immediate / Urgent / Routine** and quote both clocks. The trade-off is not
invented — it is policy, with a 10-versus-25-business-day gap, and the tenant answer can cite it.

### 2.2 NSW (Homes NSW)

**Three tiers with timeframes exist only on legacy pages; the live page has collapsed to two tiers
with no clocks.** Legacy `housing.nsw.gov.au` material: "Two to eight hours" for critical problems
"involving health, safety or security concerns, such as electrical hazards, gas leaks, or
flood/sewer overflows in common areas"; "Twenty-four to 48 hours" for urgent problems "such as no
internal working lights, blocked external drains, or stoves or hot water heaters not working";
"Twenty days" for general repairs. The current nsw.gov.au "Homes NSW maintenance service" page names
only **Emergency maintenance** ("Flooding from a burst water pipe", "Raw sewerage overflowing inside
your home", "A gas leak", "Fire damage to a property"; "call the Maintenance Hub immediately: 1800
422 322") and **Non-urgent maintenance** via MyHousing Repairs, with "All requests made through
MyHousing Repairs are reviewed before processing" — **no timeframes**.
*nsw.gov.au "Homes NSW maintenance service"; facs.nsw.gov.au "Requesting maintenance and reporting
problems" and "/maintenance/response-times" (the latter 302-redirects to the overview as of
2026-09-14). All undated.* **Contradiction:** treat the three-tier numbers as historical.
→ Fair Turn: "All requests … are reviewed before processing" is the real-world counterpart of the
Review queue, in a government's own words.

### 2.3 New Zealand (Kāinga Ora)

**Two tiers, a 4-hour urgent target hedged with "wherever possible", and a visit-first promise for
non-urgent.** "Urgent repairs are problems that affect your health and safety, and Kāinga Ora will
fix these **within 4 hours, wherever possible**", examples "blocked drains or sewage problems, gas
leaks or bad water leaks, no power or hot water, electrical faults, no stove top elements working,
and faulty smoke detectors". Non-urgent: "we'll get a contractor to visit **within 10 working days**
to check what is needed" — an *assessment*, not a fix; logged "online using MyKāingaOra anytime".
*Kāinga Ora, "Maintaining your home" and "Maintenance and repairs" factsheet PDF (undated).*
→ Fair Turn: the honest promise is "someone will look at it by X", not "it will be fixed by X". The
tenant answer should distinguish assessment from repair.

### 2.4 UK councils — the tenant-facing status surface

**Emergencies are deliberately routed off the online channel; the online channel is where tracking
lives.** Hull names **Emergency repairs** (same day; "locked out of property", "no heating or hot
water during extreme weather", "total loss of power, water or gas", "damaged door or window has
left your home insecure", "severe leaks or burst pipes") and **Urgent UI5** (within 5 working days;
"loss of hot water where no occupant is at risk", "minor plumbing such as a leak that can be
contained", "leaking roofs", "glazing where there is no security risk"). Emergencies "can only be
reported by telephoning 01482 300 300", with a fairness warning in plain words: "**If you misreport
a problem to get a quicker response, it stops us from responding quickly to real emergencies**".
Croydon, Luton and Hull all instruct tenants not to report emergencies online. Camden runs a
tracker at `housing-repairs.camden.gov.uk/track` ("Find your repair"): "You can track repairs
online even if you reported the repair another way, and to change or cancel it, use WhatsApp, SMS
or live chat." Islington: "you will receive a text containing a link to track their arrival" on the
day. Haringey: "you can check on the status of a repair and rebook appointments using Housing
Online."
*Hull "Repairs"; Camden "Report a housing repair" / "Find your repair"; Islington "Report a repair
in your home"; Haringey "Check the progress of a repair"; Croydon and Luton repairs pages. All
undated.* **TBD — needs validation:** the exact status *names* inside these portals (login-gated).
→ Fair Turn: a job number → answer lookup with no login is the right shape, and should answer what
every council exposes: what state it is in, when someone is expected, what the tenant can do next.

---

## 3. Triage-queue UX in operational tools

**A triage queue is a named place in the navigation with its own keyboard entry, reviewed one item
at a time, with a small closed set of verbs.** Linear: **Triage** appears "under the team name in
the sidebar"; reached with `G` then `T`, or `O` then `T`. **Accept** (`1`) — "Accepting an issue
will offer the option to leave a comment and then move the issue to your team's default status";
**Mark as duplicate** (`2` or `MM`); **Decline** (`3`) — updates to a "Canceled status type" and
"present[s] the option of adding a comment with an explanation"; **Snooze** (`H`) — "hide the issue
from the triage queue to return at a time of your choosing, **or when there's new activity on that
issue: whichever comes first**". *Linear Docs, "Triage" (undated).*
→ Fair Turn: four verbs maximum in the Review queue, each on a digit key, each offering a comment.
Fair Turn's difference: the comment is **required**, not offered.

**The list has a "work the queue" mode that hands the operator the next item on submit — and it can
be made mandatory.** Zendesk: "You press the **Play** button or icon in a ticket view to open the
first ticket in the view… After addressing the ticket, click **Submit** to update it and
automatically move to the next available ticket." **Guided mode** "helps you manage ticket order by
restricting agents to using the Play button to navigate through tickets", and on Enterprise plans
"automatically launches Play mode when an agent opens a view". *Zendesk Help, "Using Play mode to
quickly work through tickets"; "Setting up Guided mode" (undated).*
→ Fair Turn: a "Start review" button that walks the queue and returns after each save turns the
Review queue from a list into a session with an end.

**Urgency and priority are deliberately separated: one orders the work, the other decides who gets
woken up.** PagerDuty: "**Priority** is tied to incidents and specifies the order in which
incidents must be addressed (for example, P1, Sev-1)"; "**Urgency** … determines how you are
notified when an incident is assigned to you (high or low)". The list has an **Urgency** column
"with high-urgency incidents appearing at the top"; status filter "Open, Triggered, Acknowledged,
Resolved, or Any Status"; **Sort By** → "Urgency, Priority, or Recent". Every change is confirmed:
"tap **Add/Edit Priority**, select a priority level, and tap **Confirm**". *PagerDuty Support,
"Incident Priority", "Navigate the Incidents Page", "Edit Incidents" (undated).*
→ Fair Turn: two axes — *policy class* (Immediate/Urgent/Routine, from NT) and *today's rank* — are
legitimately different columns. Both shown makes an override legible: "Urgent by policy, rank 14
today, because …". And every priority change is confirmed, never a silent inline edit.

**A "needs attention" queue is defined by machine-checkable conditions and cleared by a real
action, not a dismissal.** ServiceM8's Action Required states its three membership conditions
(§1.5); exit is reschedule, queue, set status, or reply — no "dismiss" that merely hides.
→ Fair Turn: state the Review queue's membership rule on the page — "a required field could not be
grounded in the tenant's own words" — and make setting the field with a reason the only exit.

---

## 4. Equity-aware allocation interfaces — published work

**How an allocation is framed and visualised measurably changes how fairly people allocate — so
framing is a design decision, not neutral chrome.** From the abstract: "cognitive biases can hinder
the fair allocation of resources… This work investigates whether the design of interactive resource
allocation tools can help to promote allocation fairness. We specifically study the effect of
presentation format (using text or visualization) and a specific framing strategy (showing
resources allocated to **groups or individuals**)… **Our main finding indicates that
individual-framed visualizations and text may be able to curb unfair allocations caused by
group-framed designs.**" The instrument was a slider splitting money between two fictional programs
benefiting two distinct communities.
*Verma, Morais, Dragicevic, Chevalier, CHI 2023 (Hamburg, 23–28 April 2023); arXiv:2409.06688,
submitted 10 September 2024. The ACM DOI page returned HTTP 403 on 2026-09-14; abstract from arXiv.*
→ Fair Turn: show the effect **per household**, not only per region — "3 households in Region B
wait 11 more days" beats "Region B share falls 4%". Most actionable finding here.

**Letting stakeholders build and inspect the weighting improves both perceived procedural fairness
and the distribution itself, in a real allocation service.** WeBuildAI "enable[s] stakeholders to
construct a computational model that represents their views and to have those models vote on their
behalf to create algorithmic policy", applied to the matching algorithm of 412 Food Rescue, an
on-demand food donation transportation service. The process "improved both procedural fairness and
distributive outcomes", enhancing trust, and demonstrated stakeholder involvement "balancing equity
and efficiency in donation distribution".
*Min Kyung Lee et al., "WeBuildAI: Participatory Framework for Algorithmic Governance", Proc. ACM
Human-Computer Interaction 3, CSCW, Article 181, 2019.*
→ Fair Turn: the weight set by the coordinator *and recorded* is the defensible pattern; the audit
log is what makes it procedural rather than arbitrary.

**Public-sector practitioners ask for tools that let them justify a decision to someone else — a
different requirement from explaining the model.** 27 public sector machine learning practitioners
across five OECD countries were interviewed; the paper identifies opportunities for "building
usable transparency tools to identify risks and incorporate domain knowledge, aimed both at
managers and at the '**street-level bureaucrats**' on the frontlines of public service", and finds
current fairness research does not address practitioners' real operational constraints.
*Veale, Van Kleek, Binns, CHI 2018 (21–26 April 2018); arXiv:1802.01029, submitted 3 Feb 2018.*
→ Fair Turn: the coordinator is the street-level bureaucrat; what they need is a defence they can
hand upward and outward — the sign-off record plus the tenant answer.

**There is a formal justification for choosing a policy *before* knowing which side you land on.**
The paper "takes the perspective of a rational, risk-averse individual who is going to be subject
to algorithmic decision making and is faced with the task of choosing between several algorithmic
alternatives **behind a Rawlsian veil of ignorance**", proposing welfare-based fairness measures on
that basis. *Heidari, Ferrari, Gummadi, Krause, NeurIPS 2018; arXiv:1806.04959, 13 June 2018.*
→ Fair Turn: the citation behind "set the weight before you see today's list". **TBD:** no UI study
found testing a set-policy-first interaction; present it as a principled design choice.

---

## Usage logic a coordinator would recognise

Built only from what the sources above show; each step names its source.

1. **Read the day's numbers before any job.** Salesforce's KPI bar (scheduled time, average travel,
   count in jeopardy); ServiceNow's Dispatcher Dashboard (critical pending, SLAs breached). (§1.1, §1.2)
2. **Clear what came back overnight.** ServiceM8's Action Required collects jobs with no future
   booking, jobs expired from a queue, and unanswered client messages; Maximo frames dispatching as
   reacting to unplanned events. (§1.5, §1.4)
3. **Work the triage queue one at a time until empty.** Zendesk Play mode opens the first item and
   moves to the next on Submit; Linear Triage is one issue at a time with four digit-key verbs. (§3)
4. **Snooze, don't drop, what cannot be decided now.** Linear's snooze returns on a chosen time or
   on new activity; ServiceM8 queues carry a default expiry date. (§3, §1.5)
5. **Choose the day's scheduling policy.** Salesforce's Policy selector; Dynamics' per-board
   optimisation goal. A setting chosen *before* scheduling. (§1.1, §1.3)
6. **Filter to the territory being worked.** Salesforce's Filter by Territory; ServiceNow filters
   task panel, schedule and map together on assignment group. (§1.1, §1.2)
7. **Ask for candidates rather than letting it book.** Dynamics' Suggest resources (Preview) vs Book
   resources (Preview); Maximo's dialog before Assign; ServiceNow's Rank Resources. (§1.3, §1.4, §1.2)
8. **Read each candidate against named criteria.** ServiceNow's Matching Skills / Available Parts /
   Distance to Task; Salesforce's "closest available mobile workers" in minutes away. (§1.2, §1.1)
9. **Open a job and read the side panel.** ServiceNow's contextual side panel; Dynamics' Details
   panel for the selected booking, resource or requirement. (§1.2, §1.3)
10. **Use the map to see the geography of the day.** Salesforce's territory polygons and traffic;
    ServiceNow's clustered pins with counts; Dynamics' drag from map pin to timeline. (§1.1–§1.3)
11. **Override by hand where the plan is wrong.** Drag-and-drop on the timeline (Salesforce,
    Dynamics, Simpro, Maximo), or right-click Move to / Move by / Reassign to. (§1.1–§1.5)
12. **Read the damage the override caused.** Salesforce raises a named rule violation; Dynamics
    documents that reassignment shifts the booking slot forward. (§1.1, §1.3)
13. **Write the reason.** Linear offers a comment on Accept and an explanation on Decline; ServiceM8
    clears Action Required by an action, not a dismissal. No product *requires* it. (§3, §1.5, §1.2)
14. **Confirm the commitment as a separate act.** Salesforce's Dispatch → Confirm and Dispatch;
    PagerDuty confirms every priority and urgency change. (§1.1, §3)
15. **Tell the tenant what happens next, in the promise the policy actually makes.** NT FS17: "The
    Department will organise a contractor… The contractor will then contact you to organise a
    suitable time", against Immediate 4 h / Urgent 2 business days (5 remote) / Routine 10 business
    days (25 remote). Kāinga Ora promises a *visit* within 10 working days. Camden and Islington give
    a tracker and an arrival link. (§2.1, §2.3, §2.4)

---

## Top 10 pattern recommendations for Fair Turn, ranked

1. **Make the fairness weight an explicit, per-day, named setting — call it the "optimisation
   goal".** Dynamics ships a user-changeable optimisation goal per schedule board; Salesforce ships
   a scheduling Policy selector. *(§1.3, §1.1)*
2. **Show the trade-off per household, not per region.** CHI 2023: individual-framed presentations
   curb the unfair allocations that group framing produces. *(§4)*
3. **Use NT's own category names and both clocks in the tenant answer.** Immediate / Urgent /
   Routine, with "2 business days (5 in remote housing)" and "10 business days (25 in remote
   housing)" from FS17 (10/25). *(§2.1)*
4. **Name the Review queue's membership rule on the page; make setting the field with a reason the
   only exit.** ServiceM8 states its three Action Required conditions; Homes NSW: "All requests …
   are reviewed before processing". *(§3, §1.5, §2.2)*
5. **Work the Review queue one at a time, digit-key verbs, mandatory comment.** Zendesk Play/Guided
   mode; Linear Triage (`1` Accept, `3` Decline, `H` Snooze). *(§3)*
6. **After every override, recompute and display the knock-on effect, named.** Salesforce's rule
   violation; Dynamics' documented travel recompute. Show "Job 4412 moves from rank 6 to rank 19".
   *(§1.1, §1.3)*
7. **Ship a legend covering status, priority, timeline and travel.** Dynamics publishes exactly
   those four under `… > Legend`; Simpro puts a status legend at the bottom of the board. *(§1.3, §1.5)*
8. **Make list, map and pane one selection.** ServiceNow's map pin → contextual side panel;
   Salesforce's Map tab on the same board; AroFlo's Timeline / Calendar / Map. *(§1.2, §1.1, §1.5)*
9. **Give deferred jobs a return date, not just a lower rank.** ServiceM8 queues carry an expiry
   date and a yellow dot for "in a queue, or has expired from a queue"; Linear snooze returns on
   time or new activity. A deprioritised remote job that silently sinks is what judges look for.
   *(§3, §1.5)*
10. **Keep sign-off a separate, confirmed act, with a two-axis display behind it.** Salesforce's
    Dispatch → Confirm and Dispatch; PagerDuty's Priority vs Urgency columns with confirm dialogs.
    Show policy class and today's rank as two columns, then freeze. *(§1.1, §3)*

---

### Open items carried forward

- **Status names inside UK council repair trackers** — login-gated, no primary screenshot.
- **Maximo Graphical Assignment screen regions, priority columns, colours** — IBM Docs describes
  the concept, not the UI.
- **Whether any dispatch product mandates a written justification on override** — none found across
  five products; Fair Turn's requirement is a genuine departure, state it as such.
- **Homes NSW three-tier timeframes** — legacy pages only; do not cite as current.
- **A UI study testing "set the policy before you see the outcome"** — none found.
- **GitHub notifications inbox** (§3) — not researched to primary depth.
