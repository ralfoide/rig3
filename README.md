# Rig3 #

## Description

A photo blog system that generates static html pages.

*Code license:* GNU GPL v2

Disclaimer:

* if you just want a "web album", go away and try [Rig1](http://rig.powerpulsar.com) or [gallery](http://gallery.menalto.com/).
* If you want a blog you can update via a nice web interface, go away too.
* If you like fancy web designs with AJAX everywhere, please go away and don't bother me.

If neither system fill your needs, *Rig3* might be for you if you want a system that allows you to:

* Generate static blog entries automatically from a static collection of pictures and text files.
* Uses the file system to dictate the structure:
    * Each post can be an individual file.
    * Or a directory with a text and a list of images.
    * Or an [Izumi](http://ralf.alfray.com/.izumi/WhatIsIzumi) blog entry.
* Uses a wiki-like [Izumi text syntax](http://ralf.alfray.com/.izumi/IzumiTextSyntax) to write post entries.
* Generates links on [Rig1](http://rig.powerpulsar.com) albums.
* Generates month-based pages and index page per category.
* Generates an atom feed per category.

My goal is to have a system that can scale reasonably well for a moderate personal
photo collection (say tens of thousands of pictures) served on a personal web server.


## Requirements

Requires Python 2.7.

This has never been updated to Python 3.


## Building and Usage

Review the
[configuration doc](rig3serv/misc/Configuration.txt)
and the
[installation doc](rig3serv/misc/Installation.txt).


## License

*Code license:* GNU GPL v2


~~
