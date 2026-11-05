#include <iostream>
#include <map>
#include <vector>

int main() {
  int hook_count;
  int weight_count;
  std::cin >> hook_count >> weight_count;
  std::vector<int> positions(hook_count);
  std::vector<int> weights(weight_count);
  for (int& position : positions) {
    std::cin >> position;
  }
  for (int& weight : weights) {
    std::cin >> weight;
  }

  // ways[t] 记录已处理钩码产生总力矩 t 的方案数。
  std::map<long long, long long> ways;
  ways[0] = 1;
  for (int weight : weights) {
    std::map<long long, long long> next;
    for (const auto& [torque, count] : ways) {
      for (int position : positions) {
        long long added = 1LL * position * weight;
        next[torque + added] += count;
      }
    }
    ways.swap(next);
  }

  std::cout << ways[0] << "\n";
  return 0;
}
