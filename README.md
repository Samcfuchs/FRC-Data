# FRC Data Retrieval

Various data retrieval scripts to import, clean, and save FRC data to csv files

All data is written to files in the `data` folder.

## Installation

Parts of this library use Erik Boesen's [tbapy](http://github.com/frc1418/tbapy)
library. You'll need to install it with `pip install tbapy` in order for those
scripts to work. For TeamInfo.py, you'll also need to `pip install geocoder`.

In order to use the APIs these scripts access, you'll need to obtain
authorization keys. You can get a TBA key
[here](https://www.thebluealliance.com/account/). Additionally, TeamInfo.py uses
google's geocoder API to get geographic coordinates for each team. Learn more
about the geocoding API and get a key
[here](https://developers.google.com/maps/documentation/geocoding/get-api-key).
Once you have authorization keys, add them to your environment variables as
`TBA_API_KEY` and `GOOGLE_API_KEY` respectively.

## Analytics

Once the data is saved to csv files, it can be analyzed with a number of tools.
It's simple to open in excel, but I've also used R, Tableau, TIBCO Spotfire, and
python scripts to allow deeper insights into databases of this size. I encourage
you to conduct your own exploratory data analysis and publish your findings!

## Futurity

I've worked pretty hard to ensure that these scripts are as general and
future-proof as possible, but since I don't control the APIs or databases I'm
using, there's always the possibility that a change in the future could break
these. If you're encountering errors, please feel free to create an issue or PR.
In particular, the MatchData script does a lot of preprocessing of the data from
The Blue Alliance, and as a result it needs to be updated on a yearly basis.
Unfortunately, FIRST releases it's API spec as late as week 1 competitions
sometimes, so I'm unable to update them until then.
