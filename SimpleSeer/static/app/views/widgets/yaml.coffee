SubView = require 'views/core/subview'
Template = require './templates/yaml'
Application = require 'application'
Collection = require 'collections/collection'

module.exports = class Yaml extends SubView
  template: Template
  depth: 0
  hover: undefined
  html: ''
  loc: undefined
  location: ''
  chosen: false
  json: []

  schema:
    Dashboard:
      type: 'Object'
      id:
        type: 'String'
        required: true
        help: "Dashboard Object ID as generated by MongoDB"
      name:
        type: 'String'
        required: true
        help: "Human readable name for the dashboard"
      locked:
        type: 'Boolean'
        required: true
        default: true
        help: "Lock/unlock user's ability to edit the dashboard"
      cols:
        type: 'Int'
        required: true
        default: 1
        help: "How many grid columns the dashboard spans"
      rowHeight:
        type: 'Int'
        required: false
        default: 100
        help: "How many vertical pixels the dashboard spans"
      widgets:
        type: 'Array'
        required: false
        item:
          type: 'Object'
          id:
            type: 'String'
            required: true
            help: "Widget Object ID as generated by MongoDB"
          name:
            type: 'String'
            required: true
            help: "Human readable name for the widget"
          canAlter:
            type: 'Boolean'
            required: true
            default: true
            help: "Allow/disallow user's ability to alter the widget"
          model:
            type: 'String'
            required: false
            default: 'null'
            help: "Backbone model the widget inherits"
          view:
            type: 'String'
            required: true
            help: "Backbone view the widget inherits"
          cols:
            type: 'Int'
            required: true
            default: 1
            help: "How many grid columns the widget spans"
          help: "A widget item"
          extras: false
        help: "A list of widgets that the dashboard contains"
      help: "Dashboard's contain a list of widgets"
      extras: true
    TabContainer:
      type: 'Object'
      id:
        type: 'String'
        required: true
        help: "TabContainer Object ID as generated by MongoDB"
      name:
        type: 'String'
        required: true
        help: "Human readable name for the tab container"
      context:
        type: 'String'
        required: true
        help: "Display rules of the tab container"
      navbar:
        type: 'String'
        required: true
        help: "Navbar element that contains the tab container"
      path:
        type: 'String'
        required: true
        help: "Relative URL path to the tab container"
      tabs:
        type: 'Array'
        required: false
        item:
          type: 'Object'
          model_id:
            type: 'String'
            required: true
            help: "Model Object ID as generated by MongoDB"
          name:
            type: 'String'
            required: true
            help: "Human readable name for the tab"
          view:
            type: 'String'
            required: true
            default: 'dashboard'
            help: "View type of the tab"
          icon:
            type: 'String'
            required: true
            default: '/img/icon-default.png'
            help: "Path to the icon image used in the navbar"
          selected:
            type: 'Boolean'
            required: true
            default: false
            help: "True/false if default selected tab"
          help: "A tab object"
          extras: false
        help: "A list of tabs that the tab container contains"
      help: "Tab container's contain a list of tabs"
      extras: false
    OLAP:
      type: 'Object'
      id:
        type: 'String'
        required: true
        help: "OLAP Object ID as generated by MongoDB"
      name:
        type: 'String'
        required: true
        default: 'All'
        help: "Human readable name for the OLAP"
      olapFilter:
        type: 'Object'
        criteria:
          type: 'Array'
          required: false
          item:
            type:
              type: 'String'
              required: true
              default: 'frame'
            name:
              type: 'String'
              required: false
              default: 'capturetime_epoch'
            exists:
              type: 'Int'
              required: false
              default: 1
            help: "The filter critera"
            extras: true
          help: "A list of criteria for the filtering"
        logic:
          type: 'String'
          required: true
          default: 'and'
        required: false
        help: "OLAP object that describes the OLAP filtering"
        extras: false
      help: "OLAP's contain a filtering object for data retreival"
      extras: false
  t: 0

  events: =>
    'click .button':'clickButton'

  firstTimeModal: =>
    application.modal.show
      title: "Willkommen!"
      message: "Hey there, just wanted to let you know this is your first time building this application :)"
      okMessage: 'Continue'
      throbber: false
      success: (options) => return

  clickButton: (e) =>
    e.preventDefault();
    ctlocation = $(e.currentTarget).attr('location')
    tlocation = $(e.target).attr('location')
    action = $(e.target).attr('action')
    if ctlocation == tlocation
      @location = []
      $(e.target).parents(".tree").each (o, i)=>
        @location.unshift($(i).attr('location'))
      value = @getValue(@location)

      collection = $(e.target).parents('.item.tree').attr('collection')

      if action == "add"
        if @location.length == 0
          @showAddTypeModal()
        else if @location
          console.log "Adding item into", @location

      if action == "edit"
        if @location
          console.log "Editing item @ ", @location

      if action == "delete"
        if @location
          if @location.length == 1
            if collection == 'Dashboard'
              foo = @dashboards.get(@location[0])
              @dashboards.remove(foo)
              @render()
            if collection == 'TabContainer'
              foo = @tabcontainers.get(@location[0])
              @tabcontainers.remove(foo)
              @render()
            if collection == 'OLAP'
              foo = @olaps.get(@location[0])
              @olaps.remove(foo)
              @render()
            if collection == 'Inspection'
              foo = @inspections.get(@location[0])
              @inspections.remove(foo)
              @render()
            if collection == 'Measurement'
              foo = @measurements.get(@location[0])
              @measurements.remove(foo)
              @render()


  getValue: (location) =>
    loopy = @json
    _.each location, (i) =>
      if !loopy?
        loopy = @json[i]
      else
        loopy = loopy[i]
    return loopy

  initialize: =>
    $('body').on 'mouseover', '.tree', (o) ->
      c = $(o.target).attr('class')
      if c == "button" or c == "button add" or c == "button edit" or c == "button delete" or c == "buttons"
        $(o.target).children('.buttons').css('display', 'block')
      else
        $('body').find('.tree .buttons').css('display', 'none')
        if c == "tree" or c == "item tree"
          $(o.target).children('.buttons').css('display', 'block')
        else
          $(o.target).parent('.tree').children('.buttons').css('display', 'block')

    $('body').on 'mouseleave', '.tree', (o) ->
      c = $(o.target).attr('class')
      $('body').find('.tree .buttons').css('display', 'none')


    @dashboards = new Collection([{'id':'ABC123', 'name':'Human', 'type': 'Dashboard'}, {'id':'DEF456', 'name':'Readable', 'type': 'Dashboard'}, {'id': "5047bc49fb920a538c000001",'rowHeight': 100,'name': "Image View",'widgets': [{'name' : "hello", 'id':'aaa12312312'},{'name': "Frames",'canAlter': false,'model': 'null','view': "/widgets/yaml",'cols': 1,'id': "50d0b12c3ea38e249ed47b12"}],'locked': true,'cols': 1,'type': "Dashboard"}])
    @tabcontainers = new Collection([{'id':'GHI789', 'name':'Text', 'type':'TabContainer'}])
    @olaps = new Collection([])
    @inspections = new Collection([])
    @measurements = new Collection([])

    @render()

  getButtons: (key, loc) =>
    type = undefined
    a = 0
    b = 0
    c = 0
    ret = '<div class="buttons">'
    dest = loc + "-" + key
    if String(key) != 'id'

      locArray = dest.split("-")

      if locArray.length == 3
        s = @schema[locArray[0]][locArray[2]]
        if s.type == 'Object' or s.type == 'Array'
          a++
        else
          b++
        if !s.required
          c++

      if locArray.length == 4
        s1 = @schema[locArray[0]][locArray[2]]
        if s1.type == "Array"
          a++
          c++

      if locArray.length == 5
        s1 = @schema[locArray[0]][locArray[2]]
        if s1.type == "Array"
          s = @schema[locArray[0]][locArray[2]]['item'][locArray[4]]
          if s.type == 'Object' or s.type == 'Array'
            a++
          b++
          if !s.required
            c++
          
      if a
        ret += '<span class="button add" action="add" location="' + dest + '">A</span>'
      if b
        ret += '<span class="button edit" action="edit" location="' + dest + '">E</span>'
      if c
        ret += '<span class="button delete" action="delete" location="' + dest + '">D</span>'

    ret += '</div>'
    return ret

  formatObject: (obj, loc, inherit = false, key) =>
    if inherit and key
      loc += "-" + key
    ret = ''
    for key of obj
      if typeof obj[key] is "object"
        ret += '<div class="tree" location="' + loc + '-' + String(key) + '">'
        if !isNaN(key)
          type = "list-item"
        else
          type = typeof obj[key]
        ret += '<span class="key">' + String(key) + '</span>' + ' <small>(' + type + ')</small>'
        ret += @getButtons(key, loc)
        ret += @formatObject(obj[key], loc, true, String(key))
        ret += '</div>'
      else
        if String(key) == 'type'
          # Removed "type" and placed at main container
        else
          ret += '<div class="tree" location="' + loc + "-" + String(key) + '">'
          ret += '<span class="key">' + String(key) + ':</span><span class="value">' + String(obj[key]) + "</span>"
          ret += @getButtons(key, loc)
          ret += '</div>'
    ret

  formatHTML: (json) =>
    html = ''
    for key, o of json
      loc = o.type + "-" + o.id
      html += '<div class="item tree" collection="' + '" location="' + loc + '">'
      html += '<strong>' + o.type + '</strong>'
      html += '<div class="buttons"><span class="button add" action="add" location="' + String(o.id) + '">A</span>' + '<span class="button delete" action="delete" location="' + String(o.id) + '">D</span></div>'
      html += @formatObject(o, loc)
      html += '</div>'
    return html

  getSchema: =>
    return @schema

  getData: =>
    ret = []

    _.each @dashboards.models, (i) =>
      ret.push(i.attributes)
    _.each @tabcontainers.models, (i) =>
      ret.push(i.attributes)
    _.each @olaps.models, (i) =>
      ret.push(i.attributes)
    _.each @inspections.models, (i) =>
      ret.push(i.attributes)
    _.each @measurements.models, (i) =>
      ret.push(i.attributes)
      
    return ret

  render: =>
    @html = @formatHTML(@getData())
    super()

  getRenderData: =>
    'html': @html

  afterRender: =>
    @chosenInits()
    $container = $('#widget_grid .content')
    $container.masonry
      columnWidth: 530
      itemSelector: ".item"

  createObject: (type) =>
    if type == 'Dashboard'
      @dashboards.push({'id': 'A000000000000' + @t, 'name': 'Temporary-' + @t, 'type': 'Dashboard'})
    if type == 'TabContainer'
      @tabcontainers.push({'id': 'A000000000000' + @t, 'name': 'Temporary-' + @t, 'type': 'TabContainer'})
    if type == 'OLAP'
      @olaps.push({'id': 'A000000000000' + @t, 'name': 'Temporary-' + @t, 'type': 'OLAP'})
    if type == 'Inspection'
      @inspections.push({'id': 'A000000000000' + @t, 'name': 'Temporary-' + @t, 'type': 'Inspection'})
    if type == 'Measurement'
      @measurements.push({'id': 'A000000000000' + @t, 'name': 'Temporary-' + @t, 'type': 'Measurement'})
    @t++
    @render()

  chosenInits: =>
    $('#new').chosen({
      no_results_text: "No results matched"
    }).change((event, ui) =>
      if (ui is undefined) then (ui = {selected: "_"})
      v = ui.selected
      @createObject(v)
    )
