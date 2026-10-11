# UNSW-NB15 — what we learned about the data (plain words)

The same findings as `data_facts.md`, without the technical wording. Every number comes from
`notebooks/01_eda.ipynb`.

## 1. How big is the data?

- The dataset is a list of **network connections**. A connection is one conversation between two
  computers, like opening a website.
- **175,341 connections for training** (the model learns from these) and **82,332 for testing**
  (we check the model on these).
- Each connection has **42 pieces of information** (features): how long it lasted, how many bytes
  were sent, how fast the reply came, and so on.
- Each connection is labelled as one of **10 types**: Normal, or one of 9 kinds of attack.
- **About 1 in 3** training connections is normal; the rest are attacks.
- The most common attacks are Generic, Exploits and Fuzzers. The rarest is **Worms, with only 130
  examples**, which makes it hard for a model to learn.
- **Small surprise:** the official files had their names swapped (the "testing" file was really
  the training file). We fixed that.

## 2. Is the data clean?

**Yes.** Nothing is missing and nothing is broken.

## 3. The text columns

Three columns hold words instead of numbers:
- **Protocol:** how the computers talk, for example TCP (most web traffic) or UDP (fast, like video calls).
- **Service:** what the connection was for, for example web (HTTP), email (SMTP) or file transfer (FTP).
- **State:** how the connection ended.

**Small issue:** two "state" values appear only in the test data, never in training. The model must
be told to handle values it has never seen.

## 4. Is there enough latency data for the DNN?

- **Latency** = how long the network takes to respond. It's like ping time in an online game.
- Only **TCP** connections have a latency value.
- We found **38,244 normal training connections** with latency. That's enough to train the DNN.

## 5. A cheating risk (leakage)

- Latency (`tcprtt`) is always **exactly** the sum of two other columns: `synack` + `ackdat`.
- If the DNN saw those two columns, it would just add them up. That's like being given the answer
  sheet in an exam: it would look perfect but learn nothing.
- **So we hide those two columns from the DNN.** We proved this is needed: the rule holds in 100% of rows.

## 6. Two kinds of normal speed

- Normal traffic falls into **two clear groups**:
  - **Fast:** under 1 millisecond. These are computers in the same building.
  - **Slow:** about 150 milliseconds. These are computers far away.
- A column called **TTL** (a "distance tag" on each packet) tells which group a connection belongs to.
- **Problem:** training data is 74% fast, but test data is only 46% fast, so the two don't look alike.
- **Solution:** the DNN must see the TTL column, so it knows which group each connection is in.

## 7. Packet loss: a wrong assumption

- **Packet loss** = data that got lost on the way and had to be sent again.
- We had **assumed** loss was almost always zero, and used that as the reason not to predict it.
- **That's wrong:** only 30% of normal connections have zero loss.
- But loss closely follows how much data was sent (more data means more loss, almost exactly), so
  predicting it wouldn't add much. **This still needs a decision.**

## 8. Columns that repeat each other

- Some columns carry almost the same information. For example, **bytes sent** and **packets sent**
  rise and fall together.
- We found **16 such pairs**. It isn't a problem; it's just good to know.

## What this means for later work

1. **Packet loss:** decide whether to keep "show it on the dashboard, don't predict it", with a
   new reason.
2. **DNN:** keep the TTL column so it can tell fast connections from slow ones.
3. **Live demo risk:** our lab computers will produce TTL values never seen in this dataset, so
   predictions might be off. We'll test this later.
4. **Text columns:** handle values that appear only in the test data.

## If there's only time for 3 points

1. The data is **clean and big enough**: 175k training connections, nothing missing.
2. Latency is exactly the sum of two other columns, so we **hide them from the DNN to avoid cheating**.
3. Normal traffic has **two speed groups**, fast and slow, so the DNN needs to know which group
   each connection belongs to.
