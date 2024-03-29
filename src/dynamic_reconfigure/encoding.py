# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import roslib; roslib.load_manifest('dynamic_reconfigure')
import rospy
import inspect

from dynamic_reconfigure.msg import Config as ConfigMsg
from dynamic_reconfigure.msg import ConfigDescription as ConfigDescrMsg
from dynamic_reconfigure.msg import Group as GroupMsg
from dynamic_reconfigure.msg import GroupState
from dynamic_reconfigure.msg import IntParameter, BoolParameter, StrParameter, DoubleParameter, ParamDescription

# Wrapper object for the config dictionary
class Config:
  def __init__(self, **args):
        for k, v in args.items():
            if type(v) is dict:
                self.__dict__[k] = Config(**v) 
            elif type(v) is list:
                for d in v:
                    if type(d) is dict:
                        self.__dict__[d['name']] = Config(**d) 
            else:
                self.__dict__[k] = v

  # Preserve backwards compatibility by allowing dictionary style lookup
  def __getitem__(self, key):
      if not type(key) is str:
          raise TypeError
      elif key == "groups":
          groups = []
          for k,v in self.items():
              if isinstance(v, Config):
                  groups.append(v)
          return groups
      elif not key in self.__dict__:
          raise KeyError
      else:
          return self.__dict__[key]

  def __setitem__(self, key, value):
      if not type(key) is str:
          raise TypeError
      else:
          if type(value) is dict:
              self.__dict__[key] = Config(**value)
          elif isinstance(value, Config):
              self.__dict__[key] = value 
          elif type(value) is list:
              for d in value:
                  if type(d) is dict:
                      self.__dict__[d['name']] = Config(**d)
          else:
              self.__dict__[key] = value
              self.__setparam__(key, value)

  def __setparam__(self, name, value):
      for k, v in self.items():
          if name == k:
              self.__dict__[name] = value
          elif isinstance(v, Config):
              v.__setparam__(name, value)

  def __repr__(self):
      return repr(self.__dict__)

  def update(self, *args):
      for set in args:
          try:
              for k,v in set.items():
                  self[k] = v
          except Exception as exc:
              raise exc

  # TODO:Implement proper form of items
  def items(self):
      return self.__dict__.items()

def encode_description(descr):
    msg = ConfigDescrMsg()
    msg.max = encode_config(descr.max)
    msg.min = encode_config(descr.min)
    msg.dflt = encode_config(descr.defaults)
    msg.groups = encode_groups(None, descr.config_description)
    return msg

def encode_groups(parent, group):
    group_list = []
    
    msg = GroupMsg()

    msg.name = group['name']
    msg.id = group['id']
    msg.parent = group['parent']
    msg.type = group['type']

    for param in group['parameters']:
        msg.parameters.append(ParamDescription(param['name'], param['type'], param['level'], param['description'], param['edit_method']))

    group_list.append(msg)
    for next in group['groups']:
        group_list.extend(encode_groups(msg, next))

    return group_list

def encode_config(config, flat=True):
    msg = ConfigMsg()
    for k, v in config.items():
        ## @todo add more checks here?
        if   type(v) == int:   msg.ints.append(IntParameter(k, v))
        elif type(v) == bool:  msg.bools.append(BoolParameter(k, v))
        elif type(v) == str:   msg.strs.append(StrParameter(k, v))
        elif type(v) == float: msg.doubles.append(DoubleParameter(k, v))
        elif type(v) == dict or type(v) == list or isinstance(v, Config):
            if flat is True:
                def flatten(g):
                    groups = []
                    for x in g['groups']:
                        groups.extend(flatten(x))
                        groups.append(GroupState(x['name'], x['state'], x['id'], x['parent']))
                    return groups
                msg.groups.append(GroupState(v['name'], v['state'], v['id'], v['parent']))
                msg.groups.extend(flatten(v))
            else:
                msg.groups = [GroupState(x['name'], x['state'], x['id'], x['parent']) for x in v]

    return msg

def group_dict(group):
    try:
        state = group.state
    except AttributeError:
        state = True
    if hasattr(group, 'type'):
        type = group.type
    else:
        type =''
    return {
        'id' : group.id,
        'parent' : group.parent,
        'name' : group.name,
        'type' : type,
        'state': state,
        'groups' : [],
        'parameters' : [],
    }

def decode_description(msg):
    mins = decode_config(msg.min)
    maxes = decode_config(msg.max)
    defaults = decode_config(msg.dflt)
    groups = {}
    grouplist = msg.groups

    def params_from_msg(msg):
        params = []
        for param in msg.parameters:
            name = param.name
            params.append({
               'name': name,
               'min' : mins[name],
               'max' : maxes[name],
               'default' : defaults[name],
               'type' : param.type,
               'description' : param.description,
               'edit_method' : param.edit_method,
            })
        return params

    # grab the default group
    for group in grouplist:
        if group.id == 0:
            groups = group_dict(group)
            groups['parameters'] = params_from_msg(group)
  
    def build_tree(group):
        children = []
        for g in grouplist:
            if g.id == 0:
               pass
            elif g.parent == group['id']:
               gd = group_dict(g)
               
               gd['parameters'] = params_from_msg(g)
               gd['groups'].extend(build_tree(gd))
               # add the dictionary into the tree
               children.append(gd)
        return children

    groups['groups'].extend(build_tree(groups))

    return groups

def get_tree(m, group = None):
    if group is None:
        for x in m.groups:
            if x.id == 0:
                group = x

    children = []
    for g in m.groups:
        if g.id == 0:
          pass
        elif g.parent == group.id:
            gd = group_dict(g)

            gd['groups'] = get_tree(m, g)
            children.append(gd)

    if group.id == 0:
        ret = group_dict(group)
        ret['groups'] = children
        return ret
    else:
        return children

def initial_config(msg, description = None):
    d = dict([(kv.name, kv.value) for kv in msg.bools + msg.ints + msg.strs + msg.doubles])
    def gt(m, descr, group = None):
        if group is None:
            for x in m.groups:
                if x.id == 0:
                    group = x

        children = []
        for g in m.groups:
            if g.id == 0:
                pass
            elif g.parent == group.id:
                gd = group_dict(g)

                def find_state(gr, dr):
                    for g in dr['groups']:
                        if g['id'] == gr['id']:
                            gr['state'] = g['state']
                            return
                        else:
                            find_state(gr, g)
                            return

                find_state(gd, descr)
                gd['groups'] = gt(m, descr, g)
                children.append(gd)

        if group.id == 0:
            ret = group_dict(group)
            ret['groups'] = children
            return ret
        else:
            return children

    if not msg.groups == [] and description is not None:
        d["groups"] = gt(msg, description)

        def add_params(group, descr):
            for param in descr['parameters']:
                group[param['name']] = d[param['name']]
            for g in group['groups']:
                for dr in descr['groups']:
                    if dr['name'] == g['name']:
                        add_params(g, dr)

        add_params(d['groups'], description)

    return Config(**d)

def decode_config(msg, description = None):
    d = dict([(kv.name, kv.value) for kv in msg.bools + msg.ints + msg.strs + msg.doubles])
    if not msg.groups == [] and description is not None:
        d["groups"] = get_tree(msg)
        
        def add_params(group, descr):
            for param in descr['parameters']:
                group[param['name']] = d[param['name']]
            for g in group['groups']:
                for dr in descr['groups']:
                    if dr['name'] == g['name']:
                        add_params(g, dr)

        add_params(d['groups'], description)
    
    return Config(**d)

def extract_params(group):
    params = []
    params.extend(group['parameters'])
    for next in group['groups']:
        params.extend(extract_params(next))
    return params

def get_parents(group, descriptions):
    parents = []
    for p in descriptions['group']:
        if p['id'] == group['parent']:
            parents.extend(get_parents(p, descriptions))
            parents.append(p)
    return parents
