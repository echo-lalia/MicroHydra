## The Origins of MicroHydra:
> *This is a rambling recount on the origins of MicroHydra, by echo-lalia (me)*  
> *You probably don't need to know any of this to use or contribute to MicroHydra, but I just wanted to write it down somewhere for myself, and anyone who is curious.*

<br/>

### Cardputer-MicroHydra

When I got my Cardputer in the mail, there was very little software or documentation available for it,
and M5Burner didn't even have a dedicated section for the Cardputer yet.
(In fact, I don't think the *demo firmware, or UIFlow*, for the Cardputer were made public yet).  
I started by installing MicroPython on it just to play around, and tried figuring out how to get each peripheral working.  

The demo firmware that came on the device got a lot of people (myself included) excited about the possibilities.
However, there was no way to easily extend the demo firmware, and I preferred working in MicroPython, anyways.  
I had previous experience with MicroPython on the RP2040, and hit a lot of roadblocks regarding memory usage.  
So, I knew that if I wanted to support a lot of different kinds of features in my program, I'd need to find a way to load only what was needed at any given time.

I came up with the idea of resetting the device between every app, to allow the RAM to be fully cleared each time.  
To do this, there would need to be some way to maintain some memory of what we were doing between resets.
Thankfully, the ESP32-S3 has a built-in RTC with it's own memory that doesn't reset when the main CPU does,
and MicroPython provides a really easy way to read/write from it.  

So, I designed a really simple `main.py` script that would read the RTC memory, and import whatever file it pointed to.
And, I also designed a barebones `launcher.py` that would scan for `.py` files in the `apps/` directory, and allow you to pick one.  
Once an app was picked, its path would be loaded into the RTC memory, and the device would reset.

<br/>

Initial impressions of the software were really positve, and people in the Cardputer Discord were super enthusiastic about the possibilities.  
People in the community were talking about what a potential 'ideal' software/operating system for the Cardputer might have in it.  
MicroPython is a really awesome and feature-rich project, and it made it really easy and quick to add a lot of the requested 'OS-like' features to MH.
And so I read all of the community suggestions, and just kept adding new features into the program.

The more I added the more enthusiasticly people responded to it, and so I was motivated to just keep adding more.  
Eventually, community members even started making pull requests with their own enhancements, and the software grew rapidly.

<br> 

### Supporting more devices

The project was named "Cardputer-MicroHydra" because it was intended to be the version of MicroHydra specific to the Cardputer.  
Eventually I thought I might fork the project and modify it for other devices. 
But, as the project got bigger, I realized this would take an increasingly huge amount of work, and that once I did that, 
it would become very difficult to extend community contributions to each completely separate version of MicroHydra.  

This kinda bummed me out as it seemed like once I got bored of working on the Cardputer (or M5Stack stopped selling them),
the software would almost certainly be useless. Or at the very least, the community would be fragmented.

*So*, I basically tried to polish up and 'officially' release a complete version with all of the features currently in MH (v1.0),
and got to work trying to restructure the program so that it could potentially support multiple devices.  

This sucked 😅

Working on MicroHydra is really fun for me, and I could practically spend all day doing it.
However, the original code was so specific to the Cardputer that I had to almost completely rewrite a lot of the modules and built-in apps for MH2.0. 
I also had to restructure the repository and write scripts for automating the process of assembling/exporting the device-specific builds of MH.
For the majority of the process, I wasn't even certain that my changes would ever be finished/released.

Once I was able to get the same launcher to start up on both the TDeck and the Cardputer, though, things became fun again, and all that work was very much worth it!  
At the time of writing, MH2.0 has been released, and I am again excited about the potential of this project. 
When time comes to support another new device there will probably be new challenges, but I hopefully I will not have to rewrite it again.

