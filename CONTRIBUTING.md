# Contributing to MicroHydra!

MicroHydra started with very fast and chaotic developnment, designed by one person, and with new features and complete overhauls added almost daily. 

Now that there are multiple people interested in implementing new features and improvements to MH, as well as people designing apps to be used with MH, I thought it would be best to create some contribution guidelines to help us work together more easily, and prevent things from getting broken haphazardly. 

<br/>

## Guidelines and philosophy for core MicroHydra functionality

#### One of MicroHydra's earliest goals was accessibility.   

This project aims to encourage tinkerers, makers, and developers, both experienced and completely new, to use and create apps for their Cardputers. The design for the app loading system was created with this in mind.    
By only requiring a simple .py file to be placed in the /apps folder, and restarting between apps, MH is able to support even extremely basic MP scripts, with little to no modificaiton. And more complex programs, which require additional libraries or other files, can simply point their fetch those files from a subfolder of the apps folder (or anywhere else).

Another way MicroHydra aims to be accesible, is by providing a large amount of documentation on the use of the launcher, and on the use of the libraries that come with it.    
It is a goal of mine to keep the wiki updated with answers to common questions, and provide examples, and instructions, to help new developers make apps or contributions for MH. 

And a final note on accesibility; This launcher is intended to work on "plain MicroPython". This is important because it minimizes restrictions on the version of MicroPython that MicroHydra can work with, and therefore reduces restrictions on the kinds of apps that can be made for MicroHydra.   
For example, if you had an ambitious idea for a game, and you wanted to use a display driver such as [s3lcd](https://github.com/russhughes/s3lcd) *(which is provided as a custom C module in a compiled MicroPython firmware)*.   
If MicroHydra was only available as a compiled firmware, you would be unable to combine s3lcd and MicroHydra, without compiling your own MicroPython from source. This could cause new barriers-to-entry, and pontentially prevent some very cool ideas from ever getting started.

#### Stability is highly important.

Another thing that is important for MicroHydra, is it's ability to just work without requiring a ton of technical knowledge, or troubleshooting.   
I've abandonded some really cool features for the launcher due to stablity reasons, and will probably do it again in the future. Providing something that is feature-rich and behaves like a real operating system would be very cool, but MicroHydra's primary responsibility is just to start 3rd party apps, and it needs to be good at that. 

<br/>


## Code, comments, and formatting

As mentioned above, MicroHydra was originally created quickly and messily. Not all of these suggestions are fully implemented in existing code, but these are goals for future code in MicroHydra. 

#### 
