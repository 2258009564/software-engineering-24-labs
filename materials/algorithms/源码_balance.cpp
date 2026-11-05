#include <iostream>
#include <vector>

int main() {
  int count;
  std::cin >> count;
  std::vector<int> weights(count);
  int total_weight = 0;
  for (int& weight : weights) {
    std::cin >> weight;
    total_weight += weight;
  }

  if (total_weight % 2 != 0) {
    std::cout << 0 << "\n";
    return 0;
  }

  int target = total_weight / 2;
  std::vector<long long> ways(target + 1, 0);
  ways[0] = 1;
  for (int weight : weights) {
    // 倒序更新，保证每个钩码在当前阶段最多使用一次。
    for (int sum = target; sum >= weight; --sum) {
      ways[sum] += ways[sum - weight];
    }
  }

  for (int sum = 0; sum <= target; ++sum) {
    if (sum > 0) {
      std::cout << " ";
    }
    std::cout << ways[sum];
  }
  std::cout << "\nways=" << ways[target] << "\n";
  return 0;
}
