Collection = require "./collection"
application = require '../application'
#FramelistFrameView = require './framelistframe_view'

module.exports = class FilterCollection extends Collection
  url:"/getFrames"
  _defaults:
    skip:0
    limit:20
  skip:0
  limit:20
  sortParams:
    sortkey:''
    sortorder:''
    sorttype:''
  
  initialize: (params) =>
    super()
    if params.bindFilter
      @bindFilter = params.bindFilter
    else
      @bindFilter = false
    @baseUrl = @url
    @filters = []
    if !application.settings.ui_filters_framemetadata?
      application.settings.ui_filters_framemetadata = []
    if params.view
      @view = params.view
      i = 0
      for o in application.settings.ui_filters_framemetadata
        @filters.push @view.addSubview o.field_name, @loadFilter(o.format), '#filter_form', {params:o,collection:@,append:"filter_" + i}
        i+=1
    @

  loadFilter: (name) ->
    application.filters[name]
    
  getFilters: () =>
  	if @filters.length == 0 and @bindFilter
  	  return @bindFilter.getFilters()
  	return @filters
  
  sortList: (sorttype, sortkey, sortorder) =>
    for o in @getFilters()
      if o.options.params.field_name == sortkey
        @sortParams.sortkey = sortkey
        @sortParams.sortorder = sortorder
        @sortParams.sorttype = sorttype
    return
  
  getSettings: (total=false, addParams) =>
    _json = []
    for o in @filters
      val = o.toJson()
      if val
        _json.push val
    if total
      skip = 0
      limit = @skip+@limit
    else
      skip=@skip
      limit=@limit
    _json =
      skip:skip
      limit:limit
      query:_json
      sortkey: @sortParams.sortkey || 'capturetime_epoch'
      sortorder: @sortParams.sortorder || -1
      sortinfo:
        type: @sortParams.sorttype || ''
        name: @sortParams.sortkey || 'capturetime_epoch'
        order: @sortParams.sortorder || -1
    if addParams
      _json = _.extend _json, addParams
    return _json
    
  getUrl: (total=false, addParams, dataSet=false)=>
    #todo: map .error to params.error
    if @bindFilter
      dataSet = @bindFilter.getSettings(total, addParams)
    if !dataSet
      dataSet = @getSettings(total, addParams)
    "/"+JSON.stringify dataSet

  fetch: (params={}) =>
    #console.dir _json
    total = params.total || false
    @url = @baseUrl+@getUrl(total,params['params']||false)
    if params.before
      params.before()
    super(params)
    
  parse: (response) =>
  	@totalavail = response.total_frames
  	return response.frames