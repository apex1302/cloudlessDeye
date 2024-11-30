CloudlessDeye - Early Alpha (Use at Your Own Risk!)

Welcome to CloudlessDeye, the slightly experimental tool that grabs data from your Deye solar inverter via its web interface and spits it out into a neat CSV file. Think of it as a way to track your solar power without the cloud, because who needs that pesky internet when you can keep things simple?

Features (or Things It Might Do):

* Pulls inverter data like a pro (I hope).
* Saves everything into a CSV file – the kind of file your spreadsheet dreams are made of.
* Runs in command-line mode with the --pst parameter (fancy, right?) and grabs its settings from the settings.ini file.

Important (and Slightly Scary) Notes:

This is early alpha software, tested on exactly ONE inverter: a Deye SUN600G3-EU-230. It might work for you, but… maybe not.
No guarantees – if it works, fantastic! If it doesn't, well... don't say I didn’t warn you.
Use at your own risk – I am not liable for anything. If you accidentally blow up your inverter, corrupt your data, or trigger an apocalypse, it’s all on you. I’m just here for the fun.
It’s highly recommended (read: strongly suggested) that you block your inverter’s internet access via your router. Think of it as "no internet for you!" vibes.

Disclaimer: I really, really don’t want you coming back here to blame me if things go south. So use CloudlessDeye with a smile, but don’t say I didn’t warn you. Enjoy!


********** some extra information **********

So, word on the street is that some Deye inverters have issues if they're offline, they might not reset the "today" value at night. Instead, they just roll with it, leaving this poor program clueless and crunching the wrong numbers.

If that happens, don't panic! You can easily mitigate it with your own script or by using the spreadsheet software of your choice to do the math. A little DIY magic, and you're good to go!
