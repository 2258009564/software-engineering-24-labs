#include <algorithm>
#include <iostream>
#include <vector>

int main() {
  int levels;
  std::cin >> levels;
  std::vector<std::vector<long long>> tower(levels);
  std::vector<std::vector<long long>> best(levels);
  for (int row = 0; row < levels; ++row) {
    tower[row].resize(row + 1);
    for (long long& value : tower[row]) {
      std::cin >> value;
    }
  }

  best[levels - 1] = tower[levels - 1];
  for (int row = levels - 2; row >= 0; --row) {
    best[row].resize(row + 1);
    for (int column = 0; column <= row; ++column) {
      long long left = best[row + 1][column];
      long long right = best[row + 1][column + 1];
      best[row][column] = tower[row][column];
      best[row][column] += std::max(left, right);
    }
  }

  std::cout << best[0][0] << "\n";
  int column = 0;
  for (int row = 0; row < levels; ++row) {
    if (row > 0) {
      std::cout << " ";
    }
    std::cout << tower[row][column];
    if (row + 1 < levels) {
      long long left = best[row + 1][column];
      long long right = best[row + 1][column + 1];
      // 两个后继等值时固定向左，保持输出路径可复现。
      if (right > left) {
        ++column;
      }
    }
  }
  std::cout << "\n";
  return 0;
}
