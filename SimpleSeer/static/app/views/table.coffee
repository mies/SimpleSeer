SubView = require 'views/core/subview'
application = require 'application'
template = require './templates/table'
rowTemplate = require './templates/row'
Collection = require "collections/table"
Frame = require "models/frame"

# Standardized Table View
# @TODO: Fix the sorting issue -- collection set array is in reverse order

module.exports = class Table extends SubView
  template:template
  rowTemplate:rowTemplate
  direction:-1
  insertDirection: -1
  renderComplete:false
  sortKey:'id'
  sortDirection:'desc'
  cof:false
  editable:true
  editableList:{}

  events :=>
    "click th" : "thSort"
    "change table.table input" : "changeCell"

  initialize: =>
    @rows = []
    super()

    # Setting up our initial conditions, options, variables etc
    if !@options.page?
      @options.page = "inf"
    else
      @cof = true

    # Columns
    if !@options.tableCols?
      @tableCols = [
        key: "id"
        title: "ID"
      ,
        key: "camera"
        title: "Camera"
        editable: true
        nullVal: '#'
      ,
        key: "capturetime"
        title: "Capture Time"
        editable: false
      ,
        key: "metadata-extra"
        title: "Extra"
        editable: true
        subcols: [
          key: 'metadata-extra-min'
          title: "Min"
          editable: true
          nullVal: '---'
        ,
          key: 'metadata-extra-max'
          title: "Max"
          editable: true
          nullVal: ''
        ]
      ]
    else
      @tableCols = @options.tableCols

    if @options.sortKey? and @options.sortKey
      @sortKey = @options.sortKey

    if @options.sortDirection? and @options.sortDirection
      @direction = @options.sortDirection
      if @direction == 1
        @sortDirection = 'asc'
      else 
        @sortDirection = 'desc'

    if @options.editable? and @options.editable
      @editable = @options.editable

    # Get the collection
    @collection = new Collection([],{model:Frame,clearOnFetch:@cof})
    if @sortKey == 'capturetime'
      @collection.setParam 'sortkey', 'capturetime_epoch'
    else
      @collection.setParam 'sortkey', @sortKey
    @collection.setParam 'sortorder', @direction
    @collection.fetch
      success:@updateData

    # Pick how we want to paginate this bad boy
    if @options.page == "inf"
      @on "page", @infinitePage
    else
      # @TODO: Initialize the html pagination

    return

  # Render the empty table with given @tableCols
  getRenderData: =>
    cols:@tableCols
    rows:@rows
    pageButtons:@options.page == "page"

  isEditable: (cols, key) =>
    edit = 0
    $.each cols, (k, v) ->
      if v.key == key
        if v.editable? and v.editable
          edit++
    if edit
      return true
    else 
      return false

  subCols: (key) =>
    subCols = undefined
    $.each @tableCols, (k, v) ->
      if v.key == key
        if v.subcols
          subCols = v.subcols
    return subCols

  # Render the cell
  renderCell: (value, key) =>    
    # Special cases go here? Human readable, etc.
    parentKey = key

    # Process the cell for an editable field
    if @editable
      if @isEditable(@tableCols, key)
        subcols = @subCols(key)
        if subcols
          html = '<div class="subCols">'
          $.each subcols, (k, v) =>
            key = v.key
            path = key.split('-')
            val = ''
            if value? and value and value[path[2]]? and value[path[2]]
              val = value[path[2]]
            if !val
              if v.nullVal? and v.nullVal
                placeholder = v.nullVal
              else
                placeholder = ''
            if @isEditable(subcols, key)
              args = {
                placeholder: placeholder
                type: 'text'
                name: parentKey + '-' + path[2]
                value: val
                class: parentKey + '-' + path[2]
              }
              html += '<div class="subCol"><label for="' + parentKey + '-' + path[2] + '">' + v.title + '</label>'
              html += "<input "
              $.each args, (k, v) =>
                html += k + '="' + v + '" '
              html += "/></div>"
            else
              html += '<div class="' + parentKey + '.' + key + '">' + val + '</div>';

          html += '</div>';
          value = html
        else 
          # @TODO: Pull nullval into scope here
          args = {
            placeholder: value
            type: 'text'
            value: value
            class: key
          }
          html = "<input "
          $.each args, (k, v) =>
            html += k + '="' + v + '" '
          html += "/>"
          value = html

    return value

  changeCell: (e) =>
    target = $(e.target)
    id = target.parents('tr').attr('id')
    key = target.attr('class')
    value = target.val();
    if id and key and value
      frame = @collection.get(id)
      o = key.split('-')
      if o.length > 1
        p = frame.get(o[0])
        if !p[o[1]]?
          p[o[1]] = {}
        p[o[1]][o[2]] = value
        @saveCell(frame, p, p[0])
      else
        obj = {}
        obj[key] = value
        @saveCell(frame, obj)

  saveCell: (frame, obj, key = '') =>
    if key
      frame.save {key:obj}
    else
      frame.save obj

  # Render the row
  renderRow:(row) =>
    values = []
    $.each @tableCols, (k, v) =>
      path = v.key.split('-')
      if path.length > 1
        r = row.get(path[0])
        key = v.key
        val = r[path[1]]
      else
        key = v.key
        val = row.get(path[0])

      value = @renderCell(val, key)
      r = {'class' : v.key, 'value' : value}
      values.push r

    return {id:row.id, values:values}

  # Insert a new row
  insertRow: (row, insertDirection = 1) =>
    if insertDirection == -1
      @rows.unshift @rowTemplate @renderRow(row)
    else
      @rows.push @rowTemplate @renderRow(row)
    return "Insert row"

  # Initialize persistant headers
  initializeHeaders: =>
    sh = @$el.find('thead tr.sh')
    offset = sh.offset()

    ph = @$el.find('thead tr.ph')
    ph.css('width', sh.css('width'))
    
    # @TODO: Change this so it always references @$el
    $('#slides').scroll(@updateHeaders)
    
  thSort:(e) =>
    # Click events for sorting
    key = $(e.target).attr('class')
    direction = $(e.target).attr('direction')
    unless direction
      direction = 'desc'

    if key == "capturetime"
      @collection.setParam 'sortkey', 'capturetime_epoch'
    else
      @collection.setParam 'sortkey', key
      
    @sortKey = key

    if direction == "asc"
        @collection.setParam 'sortorder', -1
        @sortDirection = 'desc'
        @direction = -1
    else 
        @collection.setParam 'sortorder', 1
        @sortDirection = 'asc'
        @direction = 1

    @collection.fetch
      filtered:true
      success: @updateData

  updateHeaders: =>
    sh = @$el.find('thead tr.sh')
    ph = @$el.find('thead tr.ph')

    # @TODO: Change this so it always references @$el
    if @dashboard? and @dashboard.locked and @dashboard.subviews.length == 1
      scrollTop = @$el.scrollTop()
    else 
      scrollTop = $('#slides').scrollTop()

    offset = sh.offset()
    
    $.each @tableCols, (k, v) ->
      th = 'th.' + v.key
      width = sh.find(th).width() + 10
      ph.find(th).css('width', width)

    if (scrollTop > offset.top)
      ph.css("visibility", "visible")
    else
      ph.css("visibility", "hidden")

  # Completed collection fetch, render the table content
  updateData: =>
    # Iterate through the collection list
    @rows = []
    _.each @collection.models, (model) =>
      @insertRow(model, @insertDirection)

    # Initialize persistant headers
    @initializeHeaders()

    @render()
    return

  # Paginate
  paginate: =>
    # @TODO: Change this so it always references @$el
    $('#slides').infiniteScroll({onPage: => @nextPage})

  appendData: =>
    @rows = []
    _.each @collection.models, (model) =>
      @insertRow(model, @insertDirection)

    @render()

  infinitePage: =>
    if @collection.lastavail == 20 
      @collection.setParam('skip', (@collection.getParam('skip') + @collection._defaults.limit))
      @collection.fetch success:@appendData
    return

  afterRender: =>
    # Add sort css
    @$el.find('th.' + @sortKey).attr('direction', @sortDirection).append('<span class="dir ' + @sortDirection + '"></span>')
    return

  # Render!
  render: =>
    t = super()
    return t