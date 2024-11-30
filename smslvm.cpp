#include <iostream>
#include <vector>
#include <map>
#include <fstream>
#include <string>
#include <algorithm>
#include <any>
#include <cstring>
#include <cctype>
#include <algorithm>
#include <stack>
#include <sstream>
#include <csignal>
#include <utility>
#include <stdexcept>

#define registry_t any
#define REG_SIZE 200

using namespace std;

/*union registry_t {
  void *r;
};*/

class Array {
private:
  int start;
  int size;
  registry_t *registry;
public:
  Array(int start_, int size_, registry_t registry_[]) {
    start = start_;
    size = size_;
    registry = registry_;
  }

  void bounds_check(int index) {
    if (index > size) {
      throw runtime_error("Array index out of bounds!\nElement " + to_string(index) + "was accessed, but the array only has a size of " + to_string(size));
  }
  }
  
  any get(int index) {
    bounds_check(index);
    return registry[start+index];
  }

  void set(int index, any value) {
    bounds_check(index);
    registry[start+index] = value;
  }
  int get_size() {
    return size;
  }
};


typedef struct split_vector_t_struct {
  vector<unsigned char> v1;
  vector<unsigned char> v2;
} split_vector_t;

typedef struct instruction_struct {
  unsigned char opcode;
  vector<string> args;
} instruction;

typedef struct function_struct {
  vector<instruction> code;
  vector<string> params;
} func_t;

vector<unsigned char> file_contents;
registry_t registry[REG_SIZE] = {0};
vector<string> consts;
map<string, string> vars;
vector<instruction> code;
vector<func_t> funcs;
stack<any> return_stack;
vector<Array> arrays;
unsigned char opcodes[] = {4, 5, 6, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 255};
string instructions[] = {"ADD", "LOAD_CONST", "LOAD_VAR", "WRITE", "SUB", "READ", "CAST", "STORE", "JUMP", "GT", "GTEQ", "LT", "LTEQ", "EQ", "NOTEQ", "CALL"};
bool debug_mode = false;
#define debug debug_mode


template <typename T>
T pop_front(T vector) {
  if (vector.empty())
    throw invalid_argument("empty vector");
  else
    vector.erase(vector.begin());
  return vector;
}

int any_to_int(any any_var) {
  return stoi(any_cast<string>(any_var));
}

split_vector_t split_vector(vector<unsigned char> data, unsigned char delimiter) {
  vector<unsigned char> v1;
  vector<unsigned char> v2;
  bool append_v2 = false;
  for (unsigned char& i : data) {
    if (i == delimiter)
      append_v2 = true;
    if (append_v2)
      v2.push_back(i);
    else
      v1.push_back(i);
  }
  split_vector_t result = {v1, v2};
  return result;
}

template <typename T>
vector<vector<T>> multi_split_vector(vector<T> data, T delimiter) {
  split_vector_t split;
  vector<vector<T>> result;
  while (find(data.begin(), data.end(), delimiter) != data.end()) {
    split = split_vector(data, delimiter);
    result.push_back(split.v1);
    data = split.v2;
    data = pop_front<vector<unsigned char>>(data);
  }
  return result;
}

vector<string> vector_e_to_string(vector<unsigned char> data, unsigned char delimiter) {
  string s;
  vector<string> result;
  for (int i = 0;i < data.size();i++) {
    if (data.at(i) == delimiter) {
      result.push_back(s);
      s.clear();
    }
    else {
      s += data.at(i);
    }
  }
  result.push_back(s);
  return result;
}

bool opcode_exists(unsigned char e) {
  for (int i = 0;i < sizeof(opcodes);i++)
    if (opcodes[i] == e)
      return true;
  return false;
}

vector<string> get_consts(vector<unsigned char> data) {
  string s;
  vector<string> consts;
  for (unsigned char& i : data) {
    if (i == 0) {
      consts.push_back(s);
      break;
    }
    else if (i == 1) {
      consts.push_back(s);
      s = "";
    }
    else {
      s += i;
    }
  }
  return consts;
}

map<string, string> get_vars(vector<unsigned char> data_) {
  map<string, string> vars;
  bool vars_section = false;
  bool get_var = true;
  string var = "";
  string val = "";
  for (unsigned char& i : data_) {
    if (!(vars_section || i == 0))
      continue;
    if (i == 0) {
      if (!vars_section)
	vars_section = true;
      else {
	vars[var] = val;
	break;
      }
    }
    else if (i == 1) {
      get_var = true;
      vars[var] = val;
      var.clear();
      val.clear();
    }
    else if (i == 2)
      get_var = false;
    else {
      if (get_var)
	var += i;
      else
	val += i;
    }
  }
  return vars;
}

vector<instruction> get_code(vector<unsigned char> *data_) {
  vector<unsigned char> data = *data_;
  split_vector_t split;
  vector<instruction> code;
  vector<vector<unsigned char>> code_vectors;
  bool valid_args = true;
  split = split_vector(data, '\xFE');
  if (split.v2.size() == 0)
    split.v2 = data;
  else
    split.v2 = pop_front<vector<unsigned char>>(split.v2);
  code_vectors = multi_split_vector(split.v2, (unsigned char)'\0');
  for (vector<unsigned char>& i : code_vectors) {
    if (i.size() == 0)
      continue;
    instruction instr;
    instr.opcode = i.at(0);
    string s;
    for (int j = 1;j < i.size();j++) {
      if (i.at(j) == '\1') {
	instr.args.push_back(s);
	s.clear();
      }
      else s += i.at(j);
    }
    instr.args.push_back(s);
    code.push_back(instr);
  }
  // while (split.v2.size() > 1) {
  //   instruction i;
  //   i.opcode = split.v1.at(0);
  //   split.v1 = pop_front<vector<unsigned char>>(split.v1);
  //   i.args = vector_e_to_string(split.v1, '\1');
  //   for (string& j : i.args)
  //     for (char& jj: j)
  // 	if (!isalnum(jj))
  // 	  valid_args = false;
  //   if (opcode_exists(i.opcode) && valid_args)
  //     code.push_back(i);
  //   valid_args = true;
  //   split = split_vector(split.v2, '\0');
  //   split.v2 = pop_front<vector<unsigned char>>(split.v2);
  // }
  // instruction i;
  // i.opcode = split.v1.at(0);
  // split.v1 = pop_front<vector<unsigned char>>(split.v1);
  // i.args = vector_e_to_string(split.v1, '\1');
  // if (opcode_exists(i.opcode))
  //   code.push_back(i);
  
  instruction end;
  end.opcode = 255;
  end.args = {};
  code.push_back(end);
  return code;
}

vector<func_t> get_funcs(vector<unsigned char> data) {
  vector<func_t> funcs;
  split_vector_t split;
  vector<vector<unsigned char>> func_vectors;
  
  split = split_vector(data, '\xFE');
  split = split_vector(split.v1, '\0');
  split.v2 = pop_front<vector<unsigned char>>(split.v2);
  func_vectors = multi_split_vector<unsigned char>(split.v2, '\xFD');
  for (vector<unsigned char>& i : func_vectors) {
    if (i.size() < 2)
      break;
    split = split_vector(i, '\0');
    func_t f;
    vector<string> args;
    for (unsigned char& j : split.v1) {
      string s = "";
      if (j == '\x01')
	args.push_back(s);
      else
	s += j;
    }
    split.v2 = pop_front<vector<unsigned char>>(split.v2);
    if (find(split.v1.begin(), split.v1.end(), '\1') == split.v1.end()) {
      stringstream args_stream;
      for (unsigned char& i : split.v1)
	args_stream << static_cast<char>(i);
      args.push_back(args_stream.str());
    }
    f.code = get_code(&split.v2);
    f.params = args;
    funcs.push_back(f);
  }
  return funcs;
}

string any_to_string(any var) {
  string s;
  if (var.type() == typeid(int))
    s = to_string(any_cast<int>(var));
  else if (var.type() == typeid(float))
    s = to_string(any_cast<float>(var));
  else s = any_cast<string>(var);
  return s;
}

float any_to_float(any var) {
  return stof(any_to_string(var));
}

void my_terminate() {
  cout << "Exception thrown" << endl;
}

void signal_handler(int sig) {
  cout << "Signal: " << sig << endl;
}

void print_usage() {
  cout << "Použití: smslvm <název programu> [argumenty příkazového řádku]" << endl;

}
void run(vector<string> consts, map<string, string> vars, vector<func_t> funcs, vector<instruction> code, registry_t registry[]) {
  unsigned long long idx = 0;
  instruction i;
  for (idx;idx < code.size();idx++) {
    i = code[idx];
    if (debug)
      cout << "idx: " << idx << endl;
    if (!opcode_exists(i.opcode) && i.opcode != 255)
      continue;
    if (debug)
      cout << "idx2: " << idx << endl;
    if (i.opcode == 255 && debug_mode) {
	cout << "EOF" << endl;
	break;
      }
    
    if (debug) {
      cout << "idx: " << idx << endl;      
      for (string& j : i.args)
	cout << j << ' ';
      cout << endl;
      cout << "=============================" << endl;
    }
    switch (i.opcode) {
    case 4: {; // LOAD_CONST
	if (debug_mode)
	  cout << "i.args.at(0): " << i.args.at(0) << endl;
      int const_addr = stoi(i.args.at(0));
      int reg = stoi(i.args.at(1));
      registry[reg] = any(consts[const_addr]);
      break;
    }
    case 5: {; // LOAD_VAR
      string var = vars[i.args.at(0)];
      int reg = stoi(i.args.at(1));
      registry[reg] = any(var);
      break;
    }
    case 6: { // ADD
      int reg1 = stoi(i.args.at(0));
      int reg2 = stoi(i.args.at(1));
      int dest_reg = stoi(i.args.at(2));
      try {
	registry[dest_reg] = any_to_int(registry[reg1]) + any_to_int(registry[reg2]);
      } catch (bad_any_cast) {
	registry[dest_reg] = any_cast<int>(registry[reg1]) + any_cast<int>(registry[reg2]);
      }
      break;
    }
    case 16: { // WRITE
      int reg = stoi(i.args.at(0));
      if (debug)
	cout << registry[reg].type().name() << endl;
      try {
	cout << any_cast<string>(registry[reg]);
      } catch (bad_any_cast) {
	cout << "oops, bad any cast" << endl;
      }
      break;
    }
    case 17: { // SUB
      int reg1 = stoi(i.args.at(0));
      int reg2 = stoi(i.args.at(1));
      int dest_reg = stoi(i.args.at(2));
      registry[dest_reg] = any_to_int(registry[reg1]) - any_to_int(registry[reg2]);
      break;
    }
    case 18: { // READ
      //cout << "READ" << endl;
      int reg = stoi(i.args.at(0));
      //cout << "reg: " << reg << endl;
      string value;
      cin >> value;
      registry[reg] = any(value);
      break;
    }
    case 19: { // CAST
      int reg = stoi(i.args.at(0));
      int original_type = stoi(i.args.at(1));
      int cast_type = stoi(i.args.at(2));
      int dest_reg = stoi(i.args.at(3));
      if (debug_mode)
	cout << "cast: " << registry[reg].type().name() << endl;
      switch (cast_type) {
      case 0: { // int
	if (original_type == 2) // string
	  registry[dest_reg] = any_to_int(registry[reg]);
      } // 1 - float
      case 2: { // string
        registry[dest_reg] = any_to_string(registry[reg]);
	if (debug_mode)
	  cout << "CAST (string)" << endl;
      }
      }
      break;
    }
    case 20: { // STORE
      string var_name = i.args.at(0);
      int reg = stoi(i.args.at(1));
      vars[var_name] = any_to_string(registry[reg]);
      break;
    }
    case 21: { // JUMP
      idx = stoi(i.args.at(0)); // skok na určité místo v programu
      break;
    }
    case 22: { // GT
      int reg1 = stoi(i.args.at(0));
      int reg2 = stoi(i.args.at(1));
      int out_reg = stoi(i.args.at(2));
      registry[out_reg] = any(any_to_float(registry[reg1]) > any_to_float(registry[reg2]) ? 1 : 0);
      break;
    }
    case 23: { // GTEQ
      int reg1 = stoi(i.args.at(0));
      int reg2 = stoi(i.args.at(1));
      int out_reg = stoi(i.args.at(2));
      registry[out_reg] = any(any_to_float(registry[reg1]) >= any_to_float(registry[reg2]) ? 1 : 0);
      break;
    }
    case 24: { // LT
      int reg1 = stoi(i.args.at(0));
      int reg2 = stoi(i.args.at(1));
      int out_reg = stoi(i.args.at(2));
      registry[out_reg] = any(any_to_float(registry[reg1]) < any_to_float(registry[reg2]) ? 1 : 0);
      break;
    }
    case 25: { // LTEQ
      int reg1 = stoi(i.args.at(0));
      int reg2 = stoi(i.args.at(1));
      int out_reg = stoi(i.args.at(2));
      registry[out_reg] = any(any_to_float(registry[reg1]) <= any_to_float(registry[reg2]) ? 1 : 0);
      break;
    }
    case 26: { // EQ
      int reg1 = stoi(i.args.at(0));
      int reg2 = stoi(i.args.at(1));
      int out_reg = stoi(i.args.at(2));
      registry[out_reg] = any(any_to_float(registry[reg1]) == any_to_float(registry[reg2]) ? 1 : 0);
      break;
    }
    case 27: { // NOTEQ
      int reg1 = stoi(i.args.at(0));
      int reg2 = stoi(i.args.at(1));
      int out_reg = stoi(i.args.at(2));
      registry[out_reg] = any(any_to_float(registry[reg1]) != any_to_float(registry[reg2]) ? 1 : 0);
      break;
    }
    case 28: { // AND
      int reg1 = stoi(i.args.at(0));
      int reg2 = stoi(i.args.at(1));
      int out_reg = stoi(i.args.at(2));
      registry[out_reg] = any(stoi(any_to_string(registry[reg1])) & stoi(any_to_string(registry[reg1])));
      break;
    }
    case 29: { // NOT
      int reg = stoi(i.args.at(0));
      int out_reg = stoi(i.args.at(1));
      registry[out_reg] = any(~stoi(any_to_string(registry[reg])));
    }
    case 30: { // JUMP_IF
      int reg = stoi(i.args.at(0));
      int instr = stoi(i.args.at(1));
      if (stoi(any_to_string(registry[reg])) > 0)
	idx = instr - 1;
      break;
    }
    case 31: { // LOG_NOT
      int reg = stoi(i.args.at(0));
      int out_reg = stoi(i.args.at(1));
      registry[out_reg] = any(!stoi(any_to_string(registry[reg])));
      break;
    }
    case 32: { // JUMP_IF_NOT
      int reg = stoi(i.args.at(0));
      int instr = stoi(i.args.at(1));
      if (stoi(any_to_string(registry[reg])) == 0)
	idx = instr - 1;
      break;
    }
    case 33: { // CALL
      int func = stoi(i.args.at(0));
      int return_reg = stoi(i.args.at(1));
      map<string, string> vars;
      if (i.args.size() > 2)
	for (int arg = 2;arg < i.args.size();arg++)
	  vars[funcs.at(func).params[arg-2]] = any_to_string(registry[stoi(i.args.at(arg))]);

      registry_t func_registry[REG_SIZE] = {0};
      fill(func_registry, func_registry+(REG_SIZE-1), 0);
      registry[199] = 0;
      
      run(consts, vars, funcs, funcs.at(func).code, func_registry);
      /*if (i.args.at(i.args.size()-1) == "199")
	break;*/
      registry[return_reg] = return_stack.top();
      return_stack.pop();
      break;
    }
    case 34: { // RETURN
      int reg = stoi(i.args.at(0));
      any val = registry[reg];
      return_stack.push(val);
      break;
    }
    case 35: { // JUMP
      int instr = stoi(i.args.at(0));
      idx = instr;
      break;
    }
    case 36: { // MAKE_ARRAY
      int start_address = stoi(i.args.at(0));
      int size = stoi(i.args.at(1));
      Array array = Array(start_address, size, registry);
      arrays.push_back(array);
      break;
    }
    case 37: { // GET_ELEMENT
      int array_idx = stoi(i.args.at(0));
      int elem_idx = stoi(i.args.at(1));
      int out_addr = stoi(i.args.at(2));
      registry[out_addr] = arrays[array_idx].get(elem_idx);
      break;
    }
    case 38: { // SET_ELEMENT
      int array_idx =  stoi(i.args.at(0));
      int val = stoi(i.args.at(1));
      int elem_idx = stoi(i.args.at(2));
      arrays[array_idx].set(elem_idx, val);
      break;
    }
    }
    if (idx >= code.size())
      break;
  }

}

#ifndef LIBRARY
int main(int argc, char **argv) {
  if (argc < 2) {
    print_usage();
    exit(1);
  }

  consts.reserve(10);
  FILE* csmsl_file = fopen(argv[1], "rb");
  if (csmsl_file == NULL) {
    cout << "Adresar nebo soubor nenalezen: " << argv[1] << endl;
    exit(2);
  }
  while (!feof(csmsl_file)) {
   file_contents.push_back(fgetc(csmsl_file));
   }
  /*ifstream csmsl_file;
  csmsl_file.open(argv[1], ios::binary);
  // Přejít na konec souboru
  csmsl_file.seekg(0, std::ios::end);
  // Zjistit velikost souboru
  std::streamsize size = csmsl_file.tellg();
  // Vrátit se na začátek souboru
  csmsl_file.seekg(0, std::ios::beg);

  // Vektor pro uložení dat
  std::vector<unsigned char> data(size);
  // Načtení dat
  if (!csmsl_file.read(reinterpret_cast<char*>(data.data()), size)) {
    std::cerr << "Chyba při čtení souboru." << std::endl;
    return 1;
  }
  csmsl_file.close();*/
  
  for (int j = 0;j < argc;j++)
    if (strcmp(argv[j], "-d") == 0)
      debug = true;

  //set_terminate(my_terminate);
  signal(SIGABRT, signal_handler);
  consts = get_consts(file_contents);
  funcs = get_funcs(file_contents);
  code = get_code(&file_contents);
  
  if (debug) {
    cout << "file_contents: ";
    for (unsigned char& i : file_contents)
      cout << i << ' ';
    cout << endl;
    cout << "consts: ";
    for (int i = 0;i < consts.size();i++)
      cout << consts.at(i) << " ";
    cout << endl;
    cout << "code: " << endl;
    for (instruction& i : code) {
      if (!opcode_exists(i.opcode))
	continue;
      cout << "opcode: " << i.opcode << endl;
      cout << "args: |";
      for (string& j : i.args)
	cout << j << ' ';
      cout << endl;
    }
  }
  fill(registry, registry+199, 0);
  registry[199] = 0;
  run(consts, vars, funcs, code, registry);

  cout << endl << "registry: ";
  for (int i = 0;i < 10;i++) {
    if (const string *value = any_cast<const string>(&registry[i]))
      cout << *value << ' ';
    else if (const int *value = any_cast<const int>(&registry[i]))
      cout << *value << ' ';
    else cout << "N/A ";
    //cout << registry[i].type().name() << ' ';
  }
  cout << endl;
  return 0;
}
#endif
