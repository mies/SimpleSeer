Collection = require "./collection"
application = require '../application'
Frame = require "../models/frame"
#FramelistFrameView = require './framelistframe_view'

module.exports = class FilterCollection extends Collection
  model: Frame
  url:"/getFrames"
  _defaults:
    skip:0
    limit:20
  skip:0
  limit:20
  
  initialize: (params) =>
    super()
    @filters = []
    if !application.settings.ui_filters_framemetadata?
      application.settings.ui_filters_framemetadata = []
    if params.view
      @view = params.view
    #todo: map filter sets to view type
    for o in application.settings.ui_filters_framemetadata
      @filters.push @view.addSubview o.format, application.getFilter(o.format), '#filter_form', {params:o,collection:@}
    @

  #comparator: (chapter) =>
  #  return -chapter.get("capturetime")
  #  return chapter.get("capturetime")
  
  sortList: (sortkey, sortorder) =>
    console.log sortkey
    console.log sortorder
    for o in @filters
      if o.options.params.field_name == sortkey
        @sortkey = sortkey
        @sortorder = sortorder
        @fetch()
      #console.log o.options.params.label
      #console.log o.options.params.field_name
    return
  
  fetch: (params={}) =>
    #todo: map .error to params.error
    _json = []
    for o in @filters
      val = o.toJson()
      if val
        _json.push val
    _json =
      skip:@skip
      limit:@limit
      query:_json
      sortkey: @sortkey || 'capturetime'
      sortorder: @sortorder || 1
    url = @url+"/"+JSON.stringify _json
    #console.dir _json
    $.getJSON(url, (data) =>
      #for o in data.frames
      #  console.log o.capturetime
      @.totalavail = data.total_frames
      if @skip == 0
        @reset data.frames
      else
        @add data.frames
      if params.success
        params.success(data)
      return
    ).error =>
      #todo: make callback error
      SimpleSeer.alert('request error','error')


  #filterCallback: (data) =>
    #@reset data.frames
    #for att in data.frames
    #  @add att