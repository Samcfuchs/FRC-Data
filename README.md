# Analytics
Various data retrieval scripts to import, clean, and save FRC data to csv files

All data is written to files in the `data` folder.

## Lib
The file Lib.py contains many of the methods used to retrieve data from The
Blue Alliance API. Most of these functions are documented well enough to
understand what they're doing.

## Analytics
Once the data is saved to csv files, it can be analyzed with a number of tools.
It's simple to open in excel, but I've also used R, Tableau, TIBCO Spotfire, and python scripts to allow
deeper insights into databases of this size. TeamInfo.py provides basic team
name and location information, which helps to contextualize data displays.

## Futurity
I've tried to make all of these scripts as general as possible. I'll go over 
the futurity of each one below.

### EventRanking
Should work for the forseeable future. EventRanking uses a property `sort_orders` 
provided in the TBA database to name the column headers. As long as TBA
continues to use that property consistently, this script should work without
changes. It's worth noting, however, that 2018 already had an issue, where the
data had an additional field that was not included in the sort orders. This has
been fixed.

### TeamInfo
Should work for the forseeable future. The biggest concern here is google's
geocoder API. It was a little tricky to get this fully functional, and it's
possible that a change to their quota policy could affect this script.

### TeamDivisions
Should work for the forseeable future. 
