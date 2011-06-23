#ifndef __DYNAMIC_RECONFIGURE__CONFIG_TOOLS__
#define __DYNAMIC_RECONFIGURE__CONFIG_TOOLS__

#include <string>
#include <vector>
#include <dynamic_reconfigure/Config.h>
#include <dynamic_reconfigure/Group.h>

namespace dynamic_reconfigure
{

//wrap the Group message to allow recursion
class GroupDescription : public dynamic_reconfigure::Group {
  public:
    GroupDescription(std::string n, std::string t, int p, int  i) { 
      name = n;
      type = t;
      parent = p;
      id = i;
    }

    std::vector<GroupDescription> groups;
};
 
class ConfigTools
{
public:
  static std::vector<dynamic_reconfigure::BoolParameter> &getVectorForType(dynamic_reconfigure::Config &set, const bool val)
  {
    return set.bools;
  }
  
  static std::vector<dynamic_reconfigure::IntParameter> &getVectorForType(dynamic_reconfigure::Config &set, const int val)
  {
    return set.ints;
  }
  
  static std::vector<dynamic_reconfigure::StrParameter> &getVectorForType(dynamic_reconfigure::Config &set, const std::string &val)
  {
    return set.strs;
  }
  
  static std::vector<dynamic_reconfigure::DoubleParameter> &getVectorForType(dynamic_reconfigure::Config &set, const double val)
  {
    return set.doubles;
  }
  
  static const std::vector<dynamic_reconfigure::BoolParameter> &getVectorForType(const dynamic_reconfigure::Config &set, const bool val)
  {
    return set.bools;
  }
  
  static const std::vector<dynamic_reconfigure::IntParameter> &getVectorForType(const dynamic_reconfigure::Config &set, const int val)
  {
    return set.ints;
  }
  
  static const std::vector<dynamic_reconfigure::StrParameter> &getVectorForType(const dynamic_reconfigure::Config &set, const std::string &val)
  {
    return set.strs;
  }
  
  static const std::vector<dynamic_reconfigure::DoubleParameter> &getVectorForType(const dynamic_reconfigure::Config &set, const double val)
  {
    return set.doubles;
  }
  
  static dynamic_reconfigure::BoolParameter makeKeyValuePair(const std::string &name, const bool val)
  {
    dynamic_reconfigure::BoolParameter param;
    param.name = name;
    param.value = val ;
    return param;
  }

  static dynamic_reconfigure::IntParameter makeKeyValuePair(const std::string &name, const int val)
  {
    dynamic_reconfigure::IntParameter param;
    param.name = name;
    param.value = val ;
    return param;
  }

  static dynamic_reconfigure::StrParameter makeKeyValuePair(const std::string &name, const std::string &val)
  {
    dynamic_reconfigure::StrParameter param;
    param.name = name;
    param.value = val ;
    return param;
  }

  static dynamic_reconfigure::DoubleParameter makeKeyValuePair(const std::string &name, const double val)
  {
    dynamic_reconfigure::DoubleParameter param;
    param.name = name;
    param.value = val ;
    return param;
  }

  template <class T>
  static void appendParameter(dynamic_reconfigure::Config &set, const std::string &name, const T &val)
  {
    getVectorForType(set, val).push_back(makeKeyValuePair(name, val));
  }

  template <class VT, class T>
  static bool getParameter(const std::vector<VT> &vec, const std::string &name, T &val)
  {
    for (typename std::vector<VT>::const_iterator i = vec.begin(); i != vec.end(); i++)
      if (i->name == name)
      {
        val = i->value;
        return true;
      }
    return false;
  }

  template <class T>
  static bool getParameter(const dynamic_reconfigure::Config &set, const std::string &name, T &val)
  {
    return getParameter(getVectorForType(set, val), name, val);
  }

  static int size(dynamic_reconfigure::Config &msg)
  {
    return msg.bools.size() + msg.doubles.size() + msg.ints.size() + msg.strs.size();
  }

  static void clear(dynamic_reconfigure::Config &msg)
  {
    msg.bools.clear();
    msg.ints.clear();
    msg.strs.clear();
    msg.doubles.clear();
  }
};

}

#endif
