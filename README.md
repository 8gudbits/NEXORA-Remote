# NEXORA-Remote

A phone-based remote for controlling your presentation slides over the internet.

# Preview

<div align="center">
<img src="/preview/2.png" width=250>
<img src="/preview/1.png" width=250>
</div>

## How it works

Your PC runs a small app that connects to a public MQTT broker. On your phone, you open a web page, enter a 6-digit room code, or scan a QR code and start sending left/right arrow commands. The PC picks these up and simulates the corresponding arrow key presses, so you can move forward or backward through slides in pretty much any presentation software -- PowerPoint, Google Slides, Keynote, PDF viewers, you name it.

Both devices just need an internet connection. No local network, Bluetooth, or USB cable required.

## Requirements

### PC

- Windows 10 or 11
- An internet connection
- Administrator privileges may be needed, depending on your system setup

### Phone

- Any modern browser (Chrome, Safari, Firefox)
- An internet connection

## Installation

### PC Setup

Follow the quick [2-step guide](https://nexora.noman.qzz.io) to get set up.

#### A note on administrator privileges

- **Standard Windows 10/11 setups:** Administrator privileges *may* be required for the virtual keyboard library to work system-wide -- but try running it as a normal user first, since it often works fine without elevation.
- **Restricted/corporate or school devices:** Some organizations block virtual keyboard input at a policy level. If that's the case, running as administrator won't fix it.

If the arrow keys aren't registering after running normally, try running as administrator. If they still don't work, your system's security policies are likely blocking virtual keyboard input, and unfortunately there isn't a way around that.

### Phone Setup

1. Open the Nexora Remote web page in your phone's browser.
2. Enter the 6-digit room code shown on your PC.
3. Tap **Pair**.

**— or —**

Scan the QR code on your PC screen and open the link -- you'll be connected automatically.

