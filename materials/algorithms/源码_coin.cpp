#include <iostream>
#include <vector>

int FindCounterfeit(const std::vector<int>& weights,
                    int left, int right) {
  if (left == right) {
    return left;
  }

  int half = (right - left + 1) / 2;
  long long left_weight = 0;
  long long right_weight = 0;
  for (int offset = 0; offset < half; ++offset) {
    left_weight += weights[left + offset];
    right_weight += weights[right - half + 1 + offset];
  }

  if (left_weight < right_weight) {
    return FindCounterfeit(weights, left, left + half - 1);
  }
  if (left_weight > right_weight) {
    return FindCounterfeit(weights, right - half + 1, right);
  }

  // 恰有一枚较轻假币；两组等重时，它位于奇数区间的中间。
  return left + half;
}

int main() {
  int count;
  std::cin >> count;
  std::vector<int> weights(count);
  for (int& weight : weights) {
    std::cin >> weight;
  }

  std::cout << FindCounterfeit(weights, 0, count - 1) << "\n";
  return 0;
}
