## Tasks / REWORK


*** bugs ***

- cats. not shown on interface overview

- publish entries by default (not working)
    ==> fixed


*** improve ***

- page width improvement, font size evtl. --> to test
  bg evtl.
  DUPLICATE (- improve page width for widescreen)

- evtl. use flash in regular pages

- improve page nav, list overview --> ??

- evtl. dim timeline links

- evtl. use less for css


*** to check ***

- freezer

- check/fix hint texts

- check/rework image handling

- improve the href gen./storage
  - evtl. impr. sql query ==> DONE
    --> remove href gen. from timelines

- min-height for menu --> evtl. js toggle

- improve/rework timeline preview
  - add cut after 1-2 images
        ==> DONE

- image upload, size ?


*** general ***

- update readme

- write tests :D

- rework date/time functions/norming in Page class and general
  - evtl. one field for date and time

- create overlay interface on website for easy editing,
  appears when logged-in



## NEW FEATURES

__only work on new features once the current version is actually usable again__

- make private entries

- make an edit button (when logged in)

- improve "Index/Up" page nav. button



- ~~cleanup entries/categories, new entries~~

- ~~make changelog comments~~

- ~~improve timeline w/ changelog entries~~

- ~~cleanup categorized~~

- improve tags

- ?? improve main nav., evtl. simple list, other entries ??


## Tasks

- split up devel and production version ! (after going live w/ curr. v. 2017)

- evtl. archive for older stuff

- "save" / "save and close" button

- update date checkbox

- ~~finish updated home page w/ big links etc.~~

- tags page --> ?? maybe not..

- make private entries

- cleanup CSS


### Postponed

- evtl. make link to image in image info [ref1]

- some basic language support/information
  --> add language to db entries,
      so it could be used in the template...

- fix markup in interface

- evtl. show files on overview

- include/create default-template, evtl. setup stuff, README

- optional page TOC (e.g. checkbox)

- evtl. freeze/upload buttons




## Resolved

- move login into reg. view,
  try to use decorator for login check in interface
    ==> DONE (used pre-function)

- if page no title no link shown on list view
    ==> FIXED

- no link if no title in overview
    ==> FIXED

- default type not sel. on new page
    ==> FIXED

- show on home not sel./not keeping sel.
    ==> FIXED

- cat. not keeping sel. on preview
    ==> FIXED



*** rework concept 2017-11 ***

_done as such, per 2018-04-08_

- fix page navigation
  - timeline / list switch
      ==> DONE
      timeline showing n entries
        ==> DONE (make configurable)
      list showing all entries
        ==> DONE
  - entry view
      back to timeline/list
        ==> DONE
      next/prev. entry in cat.
        ==> DONE

- cleanup config
    ==> DONE

- make default cat. configurable in config
    ==> DONE


- structure site using categories

  - Home    -- entries w/ preview
  - Notes
    - Astro     -- entries w/ preview
    - Chess
    - Comp.
      - Linux       -- maybe subcat.
      - FlightSim
      - ..
    - Gaming
    - Movies
    - ..
  - Archiv  -- tbd

- adapt backend as needed
    ==> DONE (for now

---

- __rework the current version / make it usable again... !!!__

*** focus focus focus *** :D

- add index on Home, going to Blog entries list
    ==> OBSOLETE

- evtl. remove Categorized for now?
    ==> DONE

- adapt/finish timeline cut
  - cut after one image
  - .. ?
    ==> DONE

- fix blog links on Pages list
    ==> OBSOLETE



--- old as per 2018-04-08 ---

- evtl. streamline types ?
    ==> DONE

- cleanup db columns
  --> new export/import needed for this
    ==> DONE

- auto-generate "latest" on home page
  --> changelog in db !!
    ==> DONE



--- old ---

- make next by date link [ > ] not clickable, if last
    ==> DONE

- remove pub for images (db)
    ==> DONE, still in db, evtl. I want this back

- add seconds to images datetime_norm
    ==> DONE

- make subdirs for images/galleries and import from there
  (create galleries from subdirs)
    ==> DONE

- cleanup db functions
    ==> DONE

- cleanup json/ page meta data !!
  streamline template variables (e.g. .db... !!
    ==> DONE

- simplify tags
    ==> DONE (for now)

- gallery publish doesn't work, probably err. in template
    ==> pub/unpub _must_ be two forms/routes or else cannot work
    --> doesn't work still/again!!
    ==> FIXED restriction in db query was missing (home view)

- include image publish state
    ==> OBSOLETE removed galleries, images not in db

- image edit, evtl. save all at once
    ==> OBSOLETE removed galleries, images not in db

- rework exif for pages
    ==> DONE

- adapt gallery list (interface), too cluttered
    ==> DONE

- remove image galleries (don't like it...)
  why ?
  it's unclear when to actually use a gallery and when to write
  an article, since I sometimes/often do have images in the articles...
    --> remove it from website, the feature can be kept
    --> no, "dead features" are bad, remove it totally
    ==> DONE
    --> instead possibility to add autogenerated image markdown for a
        specific directory !!
    ==> DONE
        downside is that there is no "single image view", which is kinda nice,
        but if you really want that just link the image
    --> maybe something could be done about that ?
        --> [ref1]

- overview --> new entry --> preview
  type custom (others?) changes to article
    ==> FIXED

- image preview leads to error for images from web (http://...)
    ==> FIXED

- make gallery_id writable again,
  so manual gallery creation and automatic (by directory) is possible
    ==> OBSOLETE
