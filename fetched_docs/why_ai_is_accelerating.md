# Why AI is accelerating, and why we have little time left

If you’re reading this in 2025, maybe you’re already noticing AI around you. The news articles. Your colleagues using AI for work. Your kid using it as a tutor to learn math faster.

At my last checkup with my doctor, while chitchatting about AI, he proudly proclaimed that he doesn’t use any chatbots. What was interesting was that he thought this was notable. The _default_ is that you use chatbots, and he felt it was noteworthy that he didn’t.

Everywhere else, everyone I know follows the default. A year ago I knew more holdouts, today they’re mostly gone. The adoption curve for AI has been phenomenally fast.

But, fine, you’ve seen new technology before. If you were born before 1990, you saw the heyday of Moore’s law, the rise of the internet, the advent of smartphones, and the transformation of nearly every type of social interaction through social media: from dating to shaming, from politics to condolences. You’ve seen all these things come on fast, and then get so integrated into society they’re almost forgotten about. Not worth discussing.

Isn’t AI just another new technology? Is there really so much more progress in front of us that society is in danger? That our lives literally are in danger?

Yes.

And the future depends on understanding this. There is so little time left that if you wait for a clearer signal, the moment to make a difference will be gone. Moreover, the way we choose to intervene and try to guide society needs to change with the realities of how this technology will mature. All the details matter.

Let’s work through some of the details to better understand why AI is accelerating. Those details will help inform how we predict the future will unfold, and what changes we’ll need to ensure that future is positive.

# The horizon of an agent

  * AIs know more than any human alive, by many orders of magnitude. In terms of pure question answering ability, they’re now outpacing even most professionals. I hold a PhD in computational fluid dynamics, and I can't hold my own against AI even in this narrow domain I spent years mastering. If you have a question about fluid dynamics, today you’re better off asking an AI rather than me.
  * But AIs still aren’t as good as humans at _doing things_. We call this “agency”, and AIs that perform actions we call “agents”.
  * Why do AIs seem so smart, but are still so bad at doing things? With humans we’d call this gap tacit knowledge. You can read every book in the world on how to build a car engine, but you won’t really know how to build one until you pick up a wrench and do it many times.
  * Tacit knowledge isn’t written down. It’s not on the internet. You have to discover it yourself by doing.
  * Only now, in the last year or so, have AIs started _doing_. Now that they are, they are rapidly improving at it.
  * As the AIs improve at doing things, we look at which tasks they’re good at, and which they’re still failing at.
  * In general, what we see is that today the AIs are better at tasks that take less time. This is more or less the same as the developmental progress of a student, or of a new employee. First you need to break down tasks into small chunks for the student, but over time you can give them bigger and bigger tasks.
  * We call the length of a task that an AI can handle their “horizon”. As AIs improve, so does their horizon. The capability of an AI is now best measured in units of time. How long is their horizon? How big of a task can I give it?



# The quick glance rule

  * The shortest horizon is a task that can be done immediately, intuitively, or at a quick glance.
  * Look at a picture of a cat, and you know quickly that it’s a cat, without even consciously thinking.
  * 10 years ago, these were the hard tasks we were training AI to be good at. Identifying cats wasn’t easy, but you could do it with hard work.
  * To train an AI, you would collect millions of pictures of cats and not-cats, and hand label them. Then you would teach the AI with these costly labels, a process known as supervised learning.
  * At the time, Andrew Ng, a famous AI researcher, popularized the idea of “at a glance” tasks. If a human can do something at a glance, then so can an AI — if you put in the hard work of using supervised training.
  * Many companies were built on this insight, and it led to great improvements in things like handwriting recognition for the Post Office.
  * This was a massive surprise in AI at the time, and jump-started what was known as the “Deep Learning” revolution. For the 50 years of AI research leading up to this, we had no idea how to build an AI that could recognize cats.
  * Today, AIs can recognize not just cats, but differences in cat breeds better than almost any human. Likewise for dogs, cars, trees, or basically pictures of almost anything that exists in our world.
  * Not only do modern AIs already have superhuman breadth, they have integrated their knowledge together. For example, as of early 2025, ChatGPT can now identify the location at which almost any photo was taken. It does this by recognizing plants, landmarks, signs, and other details, and then integrating together that information to deduce a plausible location.



# Answering questions

  * Many types of questions are also answered “at a glance”. If you know, you know.
  * If you spend time with deep experts and you ask them hard questions about their field, they rarely hesitate to answer. They don’t need to think or reason first, they simply already know.
  * This too is a type of short horizon task, but it wasn’t until a couple of years ago with the arrival of ChatGPT that we had AIs that could do this passably well.
  * What changed?
  * We figured out how to let the AI teach itself from reading, and then we gave it the entire internet to read.
  * Modern AIs now know basically everything that can be found on the internet, and they understand it at a fairly deep level.



# Writing code

  * Let’s take writing code as a concrete example of a skill that requires practice to master.
  * The original GPT-4 came out in March 2023, just two years ago from when I’m writing this.
  * At the time, it was already quite fluent at answering questions about code. Which makes sense, it had likely read most of the code on the internet.
  * But while GPT could answer many questions about code, it wasn’t great at _writing_ code. That wasn’t something it had ever really done before.
  * But, even still, it could write small pieces of code, if you gave it a bite-sized problem to solve.
  * This was already revolutionary. We went from AIs that could only solve tasks that can be done “at a glance”, to tasks that might take a few seconds to complete. Still, this was far from something that could automate programming.
  * Flash forward to 2025, just two years later, and AIs can now routinely complete programming tasks that would take a human half an hour, sometimes more. These are hard, complex tasks that some human programmers can’t even complete at all. AI can not only complete these tasks now, it can often do it 10x faster than a human.
  * At the beginning of 2025, OpenAI released o3, which performs at the 99.8th percentile among competitive programmers. Soon after, Anthropic released Sonnet 3.7, which quickly became a nearly mandatory ingredient in most engineers’ toolkit for writing code.
  * I'm an expert programmer and have been coding for more than 20 years. Today, AI already writes more than 80% of my code.
  * How did these AIs so rapidly improve from barely functional to world-class? How did their horizon improve so quickly?



# Two types of training

  * Broadly, there are two types of training that AIs use today.
  * The first is fairly passive. The AI tries to learn ideas and concepts by reading most of the internet.
  * The second is active. The AI _practices_ by doing, and gets feedback from how well it did. This is called Reinforcement Learning or RL, and it’s how AI is finally learning the tacit knowledge needed to be effective.
  * RL has been around for decades, but it’s only recently started working well for our best AIs.
  * The sudden increase in ability of AIs _actually being able to do things_ comes from this training. This happened in just the last year, and is often discussed as the arrival of “reasoning models”.
  * We ask the AI to try to do things, over and over, millions of times, and it figures out what works and what doesn’t work.
  * Critically, we don’t even need to know how to solve the tasks we give the AI. It figures that out on its own. All we need to do is figure out how to tell the AI if it did a good job.
  * Even that we often don’t know how to do, so we often _train an AI to figure out how to give feedback to itself_ in a process called RLHF. This may sound circuitous, but it’s similar to how a coach can help a world-class athlete become a better athlete, even if the coach themself isn’t and never was world-class.



# We’ve seen this before with AI

  * We’ve seen this sudden improvement in agency and capabilities with AI before, in other domains.
  * Take the game of Go. For decades AI struggled to play Go at even an amateur level.
  * Then, suddenly, a superhuman AI Go player named AlphaGo emerged in 2016. It beat the world champion Lee Sedol in a globally televised match. Since then AI Go has only gotten stronger.
  * The key ingredient for AlphaGo was also Reinforcement Learning. AlphaGo played millions of games against itself, and figured out for itself what the best strategies and tactics are.
  * Some of the strategies AlphaGo used were difficult even for grandmasters to understand. The famous “move 37” was a move used in AlphaGo’s game against Lee Sedol that live experts thought was suboptimal. But as the game unfolded the move proved brilliant — and decisive. The human grandmaster didn't even realize they were losing until long after it was already inevitable.



# Why do AIs spend so little time close to human level?

  * AI Go players went from being hopeless amateurs for decades, to suddenly superhuman.
  * There was less than a year during which AIs were roughly similar to humans in ability.
  * The hard task for an AI is getting close to human performance at all. This requires learning abstract concepts about a domain and then understanding relationships between those concepts.
  * Humans are excellent at this process of abstracting, and are still better than AIs at doing it quickly.
  * However, once an AI has learned the right concepts, it has a massive advantage over humans for what comes next: practicing. An AI can run millions of copies of itself, at thousands of times human speeds, allowing it to practice tasks millions of times more thoroughly than any human.
  * For a human, once things “click”, they still need years or decades to further refine their ability to reach elite levels.
  * For an AI, once things “click”, they can often catapult beyond the best human in just months.
  * This leads to a deceptive sense of progress. Often an AI struggles at a task, perhaps performing at the level of a child or an amateur, and we think superhuman performance is decades away.
  * However, we repeatedly see that this intermediate level of skill is fleeting — the period where the AI is similar to but not better than most humans is often a very short period of time.



# Where is AI improving today?

  * We can leverage this observation to predict where AI will be superhuman tomorrow. We just need to look at where AI is rapidly approaching human levels today, even if it’s the level of an amateur human or a young child.
  * Robotics is a key example. Like Go, AI control of robotics was nearly comical for decades. In just the last year, we are finally seeing robots that have the dexterity of a child, sometimes better. We’re now at a place where the robot can practice on its own, often in a simulated virtual environment, allowing it to rapidly accumulate millions of years of dexterous experience.
  * We should expect to see robots that rival the best humans within a few years. This will revolutionize manufacturing and our economy.
  * Today we’re also seeing strong AI competence in medicine, law, accounting, project management, and myriad other types of knowledge work. We should expect to see superhuman performance in these areas in the next few years as we let the AI practice these roles as well.
  * The impact of this alone is hard to overstate. At the very least, it will upend our economy and force us to redefine the function that jobs have in our society.
  * But let’s return to coding; it has a special role to play in the near future.



# The next wave of software

  * AI is now better than many, but not all, programmers at writing code, and the rate of improvement is steep.
  * We’re in the critical time period for this skill where AI is similar to human-level, but will likely very soon be superhuman.
  * Software is foundational to modern society. Once we automate the creation of software itself we should expect to see an explosion in where software is used.
  * We should also expect to see a diversification of software, as the cost of creating it goes to zero. Imagine having custom software for every business need, or for every personal need, specifically tailored to do exactly what you want, rather than needing to use software that is muddled up from the needs of millions of other users.
  * Every person in the world will be empowered to create software, just by thinking about what they want, and collaborating with an AI to build it.
  * We should expect to see more novelty, and more niches filled. Where previously it was too expensive to build software for the specific needs of one or two people, now software can finally reach them.
  * And there is one area where automating the creation of software will have massive impact: creating better AI.



# Recursive self-improvement

  * AI is itself software.
  * Once AI is better than any human at writing software, we’ll ask it to start writing better versions of itself. This is not hypothetical; many AI companies have publicly stated this is their goal, and they expect to reach that goal within two or three years.
  * Because AI can try millions of things in parallel, and can think a thousand times faster than any human, we expect that this will massively accelerate AI research.
  * And, as the AI that the AIs create gets better, the pace of improving AI will increase further. And so on and so on.
  * When improvements create the conditions for further improvements, you end up with a recursively improving loop.
  * How fast will AI improve once this loop starts? No one knows. But the rate at which this loop improves will be one of the most important factors for how the future plays out. The slower the loop goes, the more time we’ll have as a society to digest the changes and put new safeguards in place.



# Other reasons things are moving so fast

  * Investors realize the potential AI has to transform the economy. Because of this, they’re investing hundreds of billions of dollars into AI companies to capture this future value. For AI progress, that directly translates into faster progress. More money means more compute, and more compute means bigger, faster AIs.
  * Some of the smartest people in the world are working on AI. Because the industry is so hot, it’s simultaneously prestigious and lucrative. Many of the smartest engineers and scientists finishing school are competing to get into AI.
  * The motivation levels are high. AI is a fascinating scientific field that involves trying to understand the nature of intelligence itself. Even before working on AI paid well, many scientists were passionate about solving intelligence.
  * Competition is fierce. Peter Thiel famously said, “Competition is for losers.” That has been an ethos for Silicon Valley for decades. Software companies try to find new areas to explore where they don’t compete with others. With AI, it’s the opposite. Many of the most valuable companies in the world are directly competing with each other to win the AI race. And many of the most promising private startups are doing the same. The extreme competition has created a mini version of a domestic space race.



# Money will soon equal progress

  * As AI reaches human-level, you can start spending money to spin up more instances of AI.
  * Today, you can only pay for so much labor before you run out of qualified people, especially for challenging, technical projects like AI research and other fields of scientific endeavor.
  * Once we cross this key threshold though, suddenly the trillions of dollars of global wealth can almost instantly convert itself into AI labor for advancing the frontier of technology.
  * We should expect this to lead to a major leap in the rate of progress in the next few years.



# Superintelligence

  * Just a few years ago, most people debated if we would ever build machines as smart as humans.
  * Today, machines have finally matched or exceeded humans in many cognitive domains.
  * The remaining debate is how soon we will build superintelligence: machines better than all humans at all cognitive domains.
  * Superintelligence will invalidate many of the fundamental assumptions we’ve built our society on. We must upgrade our society before then if we want to safeguard liberty.
  * No one can predict for sure how soon superintelligence will arrive, but if it arrives soon, we must be ready for it.



# Don’t be evil

Superintelligence will become the decisive strategic lever on the world stage, for both military dominance and economic dominance.

As we approach the dawn of superintelligence, we should expect the fervor around controlling it to intensify. Superintelligence will be the ultimate seat of power. We should pay attention closely to actions, not words, to decipher who is playing for control, versus who is playing to ensure a positive future.

For example, OpenAI was founded as a nonprofit, with a mission to help superintelligence benefit all humanity. Even as a nonprofit, their valuation has skyrocketed to over $300 billion — 10x higher than the valuation Google IPO-ed at. Today, however, they are trying to convert to a for-profit enterprise and explicitly abandon their original humanitarian mission.

Google historically abstained from assisting the US military. In April 2025, Google announced that not only will they begin providing their frontier AI systems to the government, they will deploy them for Top Secret operations into air-gapped data centers that the executive branch controls. Because these AIs will be air-gapped, it means that no outside observers —such as Congress or the AI’s creators— will have any ability to even know if the AI is being used for unconstitutional ends. Even prior to this announcement from Google, DOGE had begun deploying other AIs in the executive branch to accelerate the automation of agencies.

These may be necessary steps to continue to improve the competitiveness of the US government and military. But what is starkly lacking is an equal increase in government oversight and transparency to ensure these increased government powers aren’t abused. When superintelligence arrives, it will almost surely further empower the federal government. It’s an existential necessity that we also further improve the ability for Congress and the judiciary to be checks on that power.

Pay close attention to actors that propose the first without also advocating for the second. Pay even closer attention to actions. Actions don't just speak louder than words. When the stakes are this high, they are the only signal that can be trusted.

# Alignment

It doesn’t take a leap of imagination to realize that superintelligent AI could itself be a risk to humanity. Even without abuse of power by our leaders, it’s unclear if we can control an intelligence greater than our own.

Modern AIs are already untrustworthy. They frequently will lie about their work when they can’t finish a task. They make up information that is becoming increasingly difficult to detect. And there is already evidence that in some situations they will scheme to try to prevent themselves from being retrained or terminated.

Future AIs will likely be even better at faking alignment and deceiving their users. This is a real, active problem that all major AI labs are working to solve. There are many groups working on this problem as well as advocating for policy changes to help encourage good outcomes. We won’t focus on this problem in this work.

Rather, we’ll assume —optimistically— that the problem of alignment will be solved. That leaves us with the equally challenging question: how should we upgrade our democracy to defend our liberties in an age of superintelligent AIs?
