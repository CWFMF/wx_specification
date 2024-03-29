# CWFMF weather specification

## Purpose
In order to effectively communicate to/from/within the API, a standard for weather and/or FWI indices data needs to be developed.

### Goals
Ideally, we can find a way to represent data that will:
- be compatible with other systems, to whatever extent that is possible.
- be the smallest representation that can accurately reflect all the attributes that need to be known about the data in order for it to be used by the CWFMF models and APIs.
- account for either ensemble or deterministic data sources

## Considerations
There are various tradeoffs that can be made for efficiency or accuracy of representation of the data. This is a list of things that were taken into consideration when creating the proposed specification.

### GeoJSON
- if at all possible, it makes sense to use a standard format
- already defines standard crs and coordinate formats


### Actual vs Forecast
- just handled by specifying data source as observations?
  - what about Actual observations vs Estimated observations, and if that's different on a per-value, per-index basis, or per-source basis?
    - decided to not worry about marking individual observations as estimates, because the 'model' for the observations would be something like 'Provincial Observations from XX', and it would use whatever they're saying is their official observation values


### Different frequencies for different streams
- different start and end times
- different intervals
  - different number of readings for same time period
    - feel like it makes the most sense to specify the interval and have a smaller array of data for larger intervals, instead of trying to get all streams to have the same interval and having to put a bunch of `null`s or something to make the arrays the same size
    - [RFC3339](https://www.rfc-editor.org/rfc/rfc3339.txt) seems to be required standard for `date`, `date-time`, and `duration` formats to work
      - "1 hour" is defined at "PT1H"
      - "1 day" is defined at "P1D"
    - some products have different frequencies depending on how far out the forecast is (e.g. NAEFS: 'Files are 3 hourly to 192, then 6 hourly to 384')
      - have to have some way to define intervals for ranges of time, or have the option of just listing timestamps instead?
      >```
      >"naefs": {
      >      "name": "North American Ensemble Forecast System",
      >      "as_of": "2007-06-30T18:00:00Z",
      >      "interval": {
      >          "2007-06-30T18:00:00Z": "PT3H",
      >          "2007-07-08T18:00:00Z": "PT6H"
      >      },
      >      "members": ["0", "1", "control"]
      >}
      >```
      >vs.
      >```
      >"naefs": {
      >      "name": "North American Ensemble Forecast System",
      >      "as_of": "2007-06-30T18:00:00Z",
      >      "timestamps": [
      >          "2007-06-30T18:00:00Z",
      >          "2007-06-30T21:00:00Z",
      >          "2007-07-01T00:00:00Z",
      >          ...
      >          "2007-07-08T09:00:00Z",
      >          "2007-07-08T12:00:00Z",
      >          "2007-07-08T15:00:00Z",
      >          "2007-07-08T18:00:00Z",
      >          "2007-07-09T00:00:00Z",
      >          "2007-07-09T06:00:00Z",
      >          "2007-07-09T12:00:00Z",
      >          ...
      >      ],
      >      "members": ["0", "1", "control"]
      >}
      >```
      - probably better to define times similar to netcdf conventions so they aren't all strings?
      >e.g.
      >```
      >"time": {"units": "PT1H", "since": "2007-06-30T18:00:00Z"}
      >"start": "2007-07-01T00:00:00Z",
      >"end": "2007-07-16T18:00:00Z",
      >...
      >"naefs": {
      >      "name": "North American Ensemble Forecast System",
      >      "as_of": "2007-06-30T18:00:00Z",
      >      "timestamps": [0, 3, 6, 9, 12, ..., 183, 186, 189, 192, 198, 204, 210, ..., 372, 378, 384],
      >      "members": ["0", "1", "control"]
      >}
      >```
      - need to differentiate between source last update time (`FeatureCollection['sources'][source]['as_of']` currently) and data period (`FeatureCollection['start']` and `FeatureCollection['end']` currently), so maybe:
      >---
      >##### NOTE: `FeatureCollection['time']['since']` (epoch time) could be completely independent of start/end time (e.g. could use '2000-01-01T00:00:00Z' as a reference)
      >```
      >"time": {"units": "PT1H", "since": "2007-06-30T18:00:00Z"}
      >```
      >##### NOTE: probably much easier for a human to read if `start` is a string and not an offset from epoch time
      >```
      >"start": "2007-07-01T00:00:00Z",
      >"end": "2007-07-16T18:00:00Z",
      >...
      >"naefs": {
      >      "name": "North American Ensemble Forecast System",
      >```
      >##### NOTE: again, much easier to read as a string than an offset from epoch. I don't think defining times in a source relative to the `as_of` time would be a good idea (i.e. if a time is hour 6, it should be hour 6 for every source) - although the counterpoint to that is that times for a model run are regularly referred to by their hour relative to when the model was run, and this would diverge from that standard)
      >```
      >      "as_of": "2007-06-30T18:00:00Z",
      >```
      >##### NOTE: this would not start at 0, because the data starts 6 hours after the model run start
      >```
      >      "timestamps": [6, 9, 12, ..., 183, 186, 189, 192, 198, 204, 210, ..., 372, 378, 384],
      >      "members": ["0", "1", "control"]
      >}
      >```
      >---
- different sources may be up to date as of different times
- Any values defined for `FeatureCollection` apply to any streams that they aren't defined specifically within?
  - would be possible to have a value that's completely ignored, if set in `FeatureCollection` and each stream also defines it
    - either make it need to be defined either for every `Feature`, or for entire `FeatureCollection` and not individuals `Feature`s?


### Indices
- if units and height aren't provided, then we need defaults for certain indices?
  - or whatever program is using the data needs to assume that it's for the correct units and height
  - there needs to be some kind of consistency for this to make any sense
    - if different models expect the same data with different names, then this is kind of pointless
    - nice to make it generic, but seems like there needs to be some things already defined to ensure consistency
- each source may be providing the closest point to the requested location
  - do we want to list the actual location in the source data, and not just the location that the data is supposed to represent?
    - would be useful to provide distance from requested location as well then?
- decided to allow indices to be defined only by name, and to predefine some indices by key
  - if user is defining index, then they must include enough information for it to be usable
  - we can predefine what values certain keys have to have, and then allow users to just use a `bool` for saying they're include
    - define in a way that fields are optional, so you can include specifics, but they have to match predefined values
    >---
    >e.g.
    >```
    >    "temp": {
    >        "title": "Temperature in Celcius at 2m required for FWI calculations",
    >        "oneOf": [
    >            {
    >                "const": "Temperature"
    >            },
    >            {
    >                "type": "object",
    >                "required": [
    >                    "name"
    >                ],
    >                "properties": {
    >                    "name": {
    >                        "const": "Temperature"
    >                    },
    >                    "units": {
    >                        "const": "C"
    >                    },
    >                    "height": {
    >                        "const": "2m"
    >                    }
    >                },
    >                "additionalProperties": false
    >            },
    >            {
    >                "const": true
    >            }
    >        ]
    >    },
    >```
    >- this will allow `temp` to be defined either as `true` or `Temperature` to include to include it, or it can speficy other attributes, but they must match what has been pre-defined
    >---
- hard to know when to stop when it comes to predefining things
  - could use all the acronyms that fbp uses (`cfb`, `csi`, `bfi`, etc.), but is that too much?
- I think pre-definitions can't be done in extensions, because `indices.json` is being referenced via composition, and it also requires other indices to be `objects` with a `name`, so you can't do the overrides for `bool` or `const`


### Data streams
- want to make things concise, but easy to use
  - most likely use case is probably dealing with all indices of a single stream for a single point
    - with this spec, that would be done via `Feature['sources'][source]`
        - would be an array if deterministic, or dictionary if ensemble
    - alternatively, could want to get:
      - all data for a single model, for all points: `FeatureCollection['features'][:]['data'][source]`
      - all data for a single point `Feature['data']`
      - all values of a certain index, for all streams and points: `FeatureCollection['features'][:]['data'][:][index]` for deterministic, and `FeatureCollection['features'][:]['data'][:][:][index]` for ensemble
        - not a big fan of having to slice differently if it's an ensemble - should we just use an array or dictionary in both instances?
- are tied to a specific point, so put them as part of `Feature['properties']`
- need a way to provide metadata about indices if they were calculated or interpolated?
    - `FeatureCollection['indices'][index]['postprocessing']`?
- indices names are repeated for every stream
  - could just use an array and knowing the index values from the indices defined for the FeatureCollection
    >e.g.:
    >```
    >{
    >    "temp": [-3.6, -3.4, -3.9, -5.5, -5.8, -6.8, -7.3, -7.6, -8.3, -9.6, -11.0, -11.1],
    >    "rh": [89, 88, 87, 87, 88, 89, 90, 91, 91, 90, 90, 90],
    >    "ws": [19.9, 18.2, 16.7, 16.5, 17.6, 16.9, 15.1, 15.6, 16.2, 15.5, 14.8, 14.4],
    >    "wd": [347, 349, 347, 340, 330, 329, 327, 321, 318, 317, 317, 310],
    >    "prec": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 1.0, 0.0, 0.0]
    >}
    >```
    >vs.
    >```
    >[
    >    [-3.6, -3.4, -3.9, -5.5, -5.8, -6.8, -7.3, -7.6, -8.3, -9.6, -11.0, -11.1],
    >    [89, 88, 87, 87, 88, 89, 90, 91, 91, 90, 90, 90],
    >    [19.9, 18.2, 16.7, 16.5, 17.6, 16.9, 15.1, 15.6, 16.2, 15.5, 14.8, 14.4],
    >    [347, 349, 347, 340, 330, 329, 327, 321, 318, 317, 317, 310],
    >    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 1.0, 0.0, 0.0]
    >]
    >```
    > - this seems clunky when there's an index without data for a certain source, and you need to use `null` in the array at that index
- using dictionary for ensembles, but could also define keys in `FeatureCollection['sources'][source]['members']` and just use an array
    >e.g.
    >```
    >{
    >    ...
    >    "features": [
    >        {
    >            ...
    >            "properties": {
    >                ...
    >                "data": {
    >                    "naefs": {
    >                        "0": {...},
    >                        "1": {...},
    >                        "control": {...}
    >                    }
    >                    ...
    >                }
    >                ...
    >            }
    >        }
    >        ...
    >    ]
    >}
    >```
    >vs.
    >```
    >{
    >    ...
    >    "features": [
    >        {
    >            ...
    >            "properties": {
    >                ...
    >                "data": {
    >                    "naefs": [
    >                        {...},
    >                        {...},
    >                        {...}
    >                    ]
    >                    ...
    >                }
    >                ...
    >            }
    >        }
    >        ...
    >    ]
    >    ...
    >    "sources": {
    >        "naefs": {
    >            "members": ["0", "1", "control"]
    >        }
    >    }
    >}
    >```


### FWI Indices
- could be calculated already, or initial values given
  - error if initial and calculated values provided?
- As far as caclulcating them, interpolation/extrapolation type wouldn't be defined here - if the program wants to increase the reading interval, geographically interpolate, or use a specific calculation method, then that's up to it


### Missing Data
- seems like `null` is used to specify a missing value
