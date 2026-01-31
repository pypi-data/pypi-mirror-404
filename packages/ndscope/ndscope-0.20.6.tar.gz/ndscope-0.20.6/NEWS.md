0.20.6
======
* Supports Arrakis data sources with grpc://... URLs
* Improved channels search
    - More responsive
    - allows globbing with '*'
    - case insensitive
    - use '-' (dash) , '_' (underscore) and ' ' (space) interchangeably as separators
    - supports character classes 
    - select multiple channels
    - channel list grabs keyboard focus when it opens
* Changing text size no longer cuts off axis labels.
* Y-axes for multiple plots in a column are aligned.
* Double-click to add channel
* Suggest most likely channel name when a channel cannot be found on the server
* add RMS as a trend option
* supports live minute trends (NDS1 only)
* trigger point now centered along X axis
* trace after trigger is shown
* causes of missed triggers fixed
* Y-axis log scale tick marks less cluttered.
* numerous fixes to cursors
* reconnects to online data sources if they are unexepectedly dropped

0.19.3
======
* add plot pulls channel from plot menu entry (#333)

0.19.2
======
* fix online freeze, range reset when adding channels

0.19.1
======
* fix cursor positions in log mode

0.19.0
======
* fix reset-on-channel-add bug, improve channel add/remove behavior
* improve channel edit interface, add ability to cancel changes
* break out channel list into separate window
* better channel list filtering with globs
* improved cursor control, add time cursors to all plots
* option to disable cursor labels
* online mode locks T=0 to right axis


0.18.0
======
* template option to set grid line alpha
* fix editing channel labels and units in channel config dialog
