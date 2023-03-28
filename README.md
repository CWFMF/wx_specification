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
  - what about Actual vs Estimated, and if that's different on a per-value, per-index basis, or per-source basis?


### Different frequencies for different streams
- different start and end times
- different intervals
  - different number of readings for same time period
    - feel like it makes the most sense to specify the interval and have a smaller array of data for larger intervals, instead of trying to get all streams to have the same interval and having to put a bunch of `null`s or something to make the arrays the same size
- different sources may be up to date as of different times
- Any values defined for `FeatureCollection` apply to any streams that they aren't defined specifically within?
  - would be possible to have a value that's completely ignored, if set in `FeatureCollection` and each stream also defines it
    - either make it need to be defined either for every `Feature`, or for entire `FeatureCollection` and not individuals `Feature`s?


### Indices
- if units and height aren't provided, then we need defaults for certain indices?
  - or whatever program is using the data needs to assume that it's for the correct units and height
- each source may be providing the closest point to the requested location
  - do we want to list the actual location in the source data, and not just the location that the data is supposed to represent?
    - would be useful to provide distance from requested location as well then?


### Data streams
- want to make things concise, but easy to use
  - most likely use case is probably dealing with all indices of a single stream for a single point
    - with this spec, that would be done via `Feature['data'][source]`
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
    e.g.:
    ```
    {
        "temp": [-3.6, -3.4, -3.9, -5.5, -5.8, -6.8, -7.3, -7.6, -8.3, -9.6, -11.0, -11.1],
        "rh": [89, 88, 87, 87, 88, 89, 90, 91, 91, 90, 90, 90],
        "ws": [19.9, 18.2, 16.7, 16.5, 17.6, 16.9, 15.1, 15.6, 16.2, 15.5, 14.8, 14.4],
        "wd": [347, 349, 347, 340, 330, 329, 327, 321, 318, 317, 317, 310],
        "prec": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 1.0, 0.0, 0.0]
    }
    ```
    vs.
    ```
    [
        [-3.6, -3.4, -3.9, -5.5, -5.8, -6.8, -7.3, -7.6, -8.3, -9.6, -11.0, -11.1],
        [89, 88, 87, 87, 88, 89, 90, 91, 91, 90, 90, 90],
        [19.9, 18.2, 16.7, 16.5, 17.6, 16.9, 15.1, 15.6, 16.2, 15.5, 14.8, 14.4],
        [347, 349, 347, 340, 330, 329, 327, 321, 318, 317, 317, 310],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 1.0, 0.0, 0.0]
    ]
    ```

- using dictionary for ensembles, but could also define keys in `FeatureCollection['data'][source]['members']` and just use an array
    e.g.
    ```
    {
        ...
        "features": [
            {
                ...
                "properties": {
                    ...
                    "data": {
                        "naefs": {
                            "0": {...},
                            "1": {...},
                            "control": {...}
                        }
                        ...
                    }
                    ...
                }
            }
            ...
        ]
    }
    ```
    vs.
    ```
    {
        ...
        "features": [
            {
                ...
                "properties": {
                    ...
                    "data": {
                        "naefs": [
                            {...},
                            {...},
                            {...}
                        ]
                        ...
                    }
                    ...
                }
            }
            ...
        ]
        ...
        "data": {
            "naefs": {
                "members": ["0", "1", "control"]
            }
        }
    }
    ```


### FWI Indices
- could be calculated already, or initial values given
  - error if initial and calculated values provided?
- As far as caclulcating them, interpolation/extrapolation type wouldn't be defined here - if the program wants to increase the reading interval, geographically interpolate, or use a specific calculation method, then that's up to it


### Missing Data
- seems like `null` is used to specify a missing value