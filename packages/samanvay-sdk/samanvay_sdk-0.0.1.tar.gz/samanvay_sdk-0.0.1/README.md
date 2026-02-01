# Samanvay SDK (Python)

A lightweight Python SDK that exposes **Samanvay Kumar Tadakamalla's** professional profile, background, and social presence through a clean, client-based API.

## About Me

<p align="center">
  <a href="https://github.com/samanvay-kumar">
    <img src="https://img.shields.io/badge/GitHub-samanvay--kumar-black?style=for-the-badge&logo=github">
  </a>
  <a href="https://www.linkedin.com/in/samanvay-kumar-tadakamalla/">
    <img src="https://img.shields.io/badge/LinkedIn-Samanvay%20Kumar-blue?style=for-the-badge&logo=linkedin">
  </a>
  <a href="https://x.com/samanvay__06">
    <img src="https://img.shields.io/badge/X(Twitter)-@samanvay__06-black?style=for-the-badge&logo=x">
  </a>
  <a href="https://leetcode.com/u/samanvay__06/">
    <img src="https://img.shields.io/badge/LeetCode-samanvay__06-orange?style=for-the-badge&logo=leetcode">
  </a>
  <a href="https://medium.com/@t.samanvaykumar">
    <img src="https://img.shields.io/badge/Medium-t.samanvaykumar-black?style=for-the-badge&logo=medium">
  </a>
  <a href="https://www.reddit.com/user/samanvay_06/">
    <img src="https://img.shields.io/badge/Reddit-samanvay__06-FF4500?style=for-the-badge&logo=reddit">
  </a>
</p>

I'm a Computer Science student exploring **AI/ML, backend systems, and generative AI** by building real projects.  
I currently study at **NIAT** and serve as the **Operations Manager of the Gen AI Club**.

---

## About the SDK

The **Samanvay SDK** is a PyPI-ready Python package that provides programmatic access to:

- Identity details  
- Education and background  
- Social & developer profiles  

All through a single client object.

---

## Installation

```bash
pip install samanvay-sdk
```

## Quick Test

Once installed, let’s make sure everything’s working.

Create a new Python file (for example `test.py`) and try this:

```python
from samanvay_sdk import Client

Sam = Client()

print("Hey! 👋 Here's a quick look at what this SDK does:\n")

print(Sam.get_name())
print(Sam.get_full_name())
print()

print(Sam.get_github())
print(Sam.get_linkedin())
print(Sam.get_twitter())
```
## 🎥 SDK Demo

A short walkthrough demonstrating the Samanvay SDK output in a terminal run. Click on it to watch

[![Watch the demo](https://res.cloudinary.com/dybpntnhv/video/upload/so_1,w_1200/Screen_Recording_2026-01-31_182452_weq2hm.jpg)](
https://res.cloudinary.com/dybpntnhv/video/upload/v1769864176/Screen_Recording_2026-01-31_182452_weq2hm.mp4
)

## SDK Methods Overview

All functionality in this SDK is exposed through a single client object.  
Each method is argument-free and returns pre-filled information.

### Identity Methods
These provide basic identity details.

- `get_name()`  
  Returns the display name.

- `get_full_name()`  
  Returns the complete legal name.

---

### Social & Developer Profiles
These methods return labeled, clickable URLs when printed in supported terminals.

- `get_github()` → GitHub profile  
- `get_linkedin()` → LinkedIn profile  
- `get_twitter()` → Twitter (X) profile  
- `get_leetcode()` → LeetCode profile  
- `get_medium()` → Medium blog  
- `get_reddit()` → Reddit profile  

---

### Background Information
These methods give more context about the author.

- `get_author_info()`  
  Returns a short professional and personal summary.

- `get_education()`  
  Returns current education details.

---

### SDK Information
Details about the SDK itself.

- `about_sdk()`  
  Explains what this SDK is and why it exists.

---

All methods can be accessed directly from the client instance and are designed to be simple, readable, and easy to explore.

# That’s it. A small SDK with a bit of personality — built on curiosity.