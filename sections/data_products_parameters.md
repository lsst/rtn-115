# Named parameters to generate for `sections/data_products.tex`

Extracted from all `{\bf \color{red} ...}` placeholders. Checked = a generator
already exists in `bin/dp2_parameters.py` (verified by grep, not by running
it — confirm output still matches before ticking off for real).

## Skymap / tracts / patches (line ~27-40)

- [x] `ntracts` (line 27)
- [x] `tractarea` (line 27)
- [x] `npatchx` (line 29)
- [x] `npatchy` (line 29)
- [x] `tractoverlap` (line 31)
- [x] `patchoverlap` (line 32)
- [x] `patcharea` (line 33, 93)
- [ ] `ncellx` (line 40)
- [ ] `ncelly` (line 40)
- [ ] `ncellpatchoverlap` (line 40)

## Raw images (line ~55-63)

- [ ] `nactivedetectors` (line 55, 70)
- [x] `nexposures` (line 56, 70)
- [x] `nraws` (line 56)
- [ ] `nrawpixx` (line 58)
- [ ] `nrawpixy` (line 58)
- [ ] `namppixx` (line 59)
- [ ] `namppixy` (line 59)
- [ ] `nexposedpixx` (line 60)
- [ ] `nexposedpixy` (line 60)
- [ ] `rawhddsize` (line 63)

## PVIs (line ~70-80)

- [ ] `npvifails` (line 71)
- [ ] `npvi` (line 72, 111, 123)
- [ ] `npvipixx` (line 75)
- [ ] `npvipixy` (line 75)
- [ ] `pvihddsize` (line 80)

## Coadds (line ~93-125)

- [ ] `patchareanooverlap` (line 93)
- [ ] `npatchpixx` (line 93)
- [ ] `npatchpixy` (line 93)
- [ ] `coaddpixsize` (line 93)
- [ ] `deepcoaddselectionfwhm` (line 109)
- [ ] `ndeepcoaddpvi` (line 111)
- [ ] `ndeepcoadd` (line 113)
- [ ] `templateCoaddFrac` (line 119, 120)
- [ ] `minTemplateCoaddPVIs` (line 120, 121)
- [ ] `minMultipleTemplateCoaddPVIs` (line 120)
- [ ] `ntemplatecoaddpvi` (line 123)
- [ ] `ntemplatecoadd` (line 125)

## Catalogs (line ~196-303)

- [ ] `nIsolatedStars` (line 196)
- [ ] `nobjectshear` (line 212)
- [x] `nssobjects` (line 264)
- [x] `nsolarsystemsources` (line 269)
- [x] `nsurveypropertymaps` (line 303)

---

## Not parameters — open TODO/questions in red text (need author input, not a script)

- line 55: `XXX; official name for campaign`
- line 55: `occasiional readout failures??`
- line 56 / 70: `XXX` (same campaign-name placeholder)
- line 61: `DESCRIBE THE OVERSCAN ETC`
- line 62: `What metadata do raw images contain? Do they have any other planes?`
- line 71: `the most common failure mode was (nfails), followed by (nfails)`
- line 105: `Is this definitely the case for all three types of coadd? I know it is for Deep Coadds, but what about the other two types?`
- line 109: `circular` (placeholder describing PSF shape assumption — confirm wording, not a numeric parameter)
