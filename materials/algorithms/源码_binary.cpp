#include <iostream>
#include <vector>

int main() {
  int size;
  long long target;
  std::cin >> size >> target;
  std::vector<long long> values(size);
  for (long long& value : values) {
    std::cin >> value;
  }

  int left = 0;
  int right = size - 1;
  while (left <= right) {
    int middle = left + (right - left) / 2;
    if (values[middle] == target) {
      std::cout << middle << " " << middle << "\n";
      return 0;
    }
    if (values[middle] < target) {
      left = middle + 1;
    } else {
      right = middle - 1;
    }
  }

  // 未命中时，right 为严格前驱，left 为严格后继。
  int predecessor = right >= 0 ? right : -1;
  int successor = left < size ? left : -1;
  std::cout << predecessor << " " << successor << "\n";
  return 0;
}
