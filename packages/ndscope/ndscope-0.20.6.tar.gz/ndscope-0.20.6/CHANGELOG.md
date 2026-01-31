# Changelog
## [0.20.6] - 2026-01-29
(changes since 0.19)
- Interface
  - Supports Arrakis data sources with grpc://... URLs
    - Uses LIGO_DATA_URL=<url> environment variable
    - supports nds://... URLS
  - Improved channels search
    - More responsive
    - allows globbing with '*'
    - case insensitive
    - use '-' (dash) , '_' (underscore) and ' ' (space) interchangeably as separators
    - supports character classes 
    - select multiple channels
    - channel list grabs keyboard focus when it opens
  - Changing text size no longer cuts off axis labels.
  - Y-axes for multiple plots in a column are aligned.
  - Double-click to add channel
  - Suggest most likely channel name when a channel cannot be found on the server
  - add RMS as a trend option
  - supports live minute trends (NDS1 only)
  - trigger improved
    - trigger point now centered along X axis
    - trace after trigger is shown
    - causes of missed triggers fixed
  - Y-axis log scale tick marks less cluttered.
  - numerous fixes to cursors
  - reconnects to online data sources if they are unexepectedly dropped

- Code
  - formatted with 'ruff'
  - uses dttlib as data source
  - drop direct dependence on NDS2 libraries
    - published versions of dttlib still depend on NDS2 in order to connect to NDS servers, but 
      it's possible to build dttlib without this dependency and create an "arrakis-only" ndscope
  - improved type annotation
  - "transactional" interaction with data requests
    - make incremental data requests that are held to form a single request with all changes
  - fixed some features that were broken in Qt 6
  - uses timing types (in most places) that can exactly represent any LIGO timestamp
  - switched to pyproject.toml for python project specification

## [0.11.1] - 2021-01-29

- fix max min trend length
- usage to stdout


## [0.11.0] - 2021-01-25

- ability to manually select trend type
- ability to set plot font size (thanks Patrick Thomas)
- ability to set black-on-white style during operation (thanks Patrick
  Thomas)


## [0.10.1] - 2020-12-22

- fix indicator of missing data


## [0.10.0] - 2020-12-22

- separate crosshair tab, with position readback
- set limits on time axis


## [0.9.0] - 2020-12-10

- online second trends
- better time axis tick labels
- new tab for manually specifying time window 
- simplified export functionality from within scope
  - export plot scent to PNG, SVG, PDF
  - export data to HDF5, MAT
  - export layout to template YAML
- ability to drop crosshair at point
- support for channel units in y-axis label
