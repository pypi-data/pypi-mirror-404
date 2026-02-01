binary_tree = """
class TreeNode:
    __slots__ = ("val", "left", "right")

    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def array_to_tree(arr, index=0):
    if index >= len(arr) or arr[index] is None:
        return None
    root = TreeNode(arr[index])
    root.left = array_to_tree(arr, index * 2 + 1)
    root.right = array_to_tree(arr, index * 2 + 2)
    return root

def tree_to_array(root):
    # BFS
    result = []
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node:
            queue.append(node.left)
            queue.append(node.right)
            result.append(node.val)
        else:
            result.append(None)
    return result

def sorted_to_bst(nums):  # returns balanced bst from a sorted list
    if not nums:
        return None
    mid = len(nums) // 2
    root = TreeNode(nums[mid])
    root.left = sorted_to_bst(nums[:mid])
    root.right = sorted_to_bst(nums[mid + 1 :])
    return root


def same_tree(p, q):
    if not p and not q:
        return True
    if not p or not q:
        return False
    if p.val != q.val:
        return False
    return same_tree(p.left, q.left) and same_tree(p.right, q.right)
"""
linked_list = """
class ListNode:
    __slots__ = ("val", "next")

    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

# prefer iterative to recursive for all these helpers
# - recursive hit depth limit real fast 
def array_to_list(arr):
    dummy = ListNode()
    curr = dummy

    for val in arr:
        curr.next = ListNode(val)
        curr = curr.next

    return dummy.next


def list_to_array(head):
    result = []
    curr = head

    while curr:
        result.append(curr.val)
        curr = curr.next

    return result

def same_list(head1, head2):
    while head1 and head2:
        if head1.val != head2.val:
            return False
        head1 = head1.next
        head2 = head2.next

    return head1 is None and head2 is None
"""
questions = {
    0: {
        "markdown": """
### Score tally
Given an array of `scores` e.g `[ '5', '2', 'C', 'D', '+', '+', 'C' ]`, calculate the total points where:
```
+  add the last two scores.
D  double the last score.
C  cancel the last score and remove it.
x  add the score
```
You're always guaranteed to have the last two scores for `+` and the previous score for `D`.

### Example
```markdown
scores = [ '5', '2', 'C', 'D', '+', '+', 'C' ]
output = 30
How:
    '5' - add 5 -> [5]
    '2' - add 2 -> [5, 2]
    'C' - cancel last score -> [5]
    'D' - double last score -> [5, 10]
    '+' - sum last two scores -> [5, 10, 15]
    '+' - sum last two scores -> [5, 10, 15, 25]
    'C' - cancel last score -> [5, 10, 15]
    
    return sum -> 30
```
""",
        "test_cases": """
test_cases = [
    [score(["5", "2", "C", "D", "+", "+", "C"]), 30],
    [score(["9", "C", "6", "D", "C", "C"]), 0],
    [score(["3", "4", "9", "8"]), 24],
    [score(["4", "D", "+", "C", "D"]), 28],
    [score(["1", "C"]), 0],
    [score(["1", "1", "+", "+", "+", "+", "+", "+", "+", "+"]), 143],
    [score(["1", "D", "D", "D", "D", "D"]), 63],
    [score(["1", "1"] + ["+"] * 1_00), 2427893228399975082452],
    [score(["1", "1"] + ["D"] * 1_00), 2535301200456458802993406410752],
    [score(["1", "1"] + ["D"] * 100_000 + ["C"] * 100_001), 1],
    [score(["1", "1"] + ["+"] * 50 + ["C"] * 30 + ["+"] * 20), 701408732],
    [score(["1", "1", "C", "D", "D", "+"] * 1000), 13000],
]
""",
        "title": "Score tally",
        "level": "Breezy",
        "code": """def score(scores: list[str]) -> int:
""",
    },
    1: {
        "markdown": """
### Repeated letters
Given a string `s` of lower-case letters. Find all substrings of `s` that contains at least three consecutive identical letters. Return an array of the indices `[start, end]` of the substrings. Order the indices by the start index in ascending order.  

### Example
```
s = "abcdddeeeeaabbbcd"
output = [[3,5], [6,9], [12,15]]
How: "abcdddeeeeaabbbed" has three valid substrings: "ddd",
"eeee" and "bbb".

```
""",
        "test_cases": """
test_cases = [
    [repeated("abcdddeeeeaabbbb"), [[3, 5], [6, 9], [12, 15]]],
    [repeated("xxxcyyyyydkkkkkk"), [[0, 2], [4, 8], [10, 15]]],
    [repeated("abcdddeeeeaabbbb" * 6), [[3, 5], [6, 9], [12, 15], [19, 21], [22, 25], [28, 31], [35, 37], [38, 41], [44, 47], [51, 53], [54, 57], [60, 63], [67, 69], [70, 73], [76, 79], [83, 85], [86, 89], [92, 95]]],
    [repeated("abcd"), []],
    [repeated("aabbccdd"), []],
    [repeated(""), []],
    [repeated("abcdefffghijkl"), [[5, 7]]],
    [repeated("abcdeffghijkl" * 100_000), []],
    [repeated("abcdeffghijkl" * 100_000 + "kkk"), [[1_300_000, 1_300_002]]],
    [repeated("kkk" + "abcdeffghijkl" * 100_000), [[0, 2]]],
    [repeated("abcdefffghijkl" * 100_000), [[5 + i, 7 + i] for i in range(0, 100_000 * 14, 14)]],
]
""",
        "title": "Repeated letters",
        "level": "Breezy",
        "code": """def repeated(s: str) -> list[list[int]]:
""",
    },
    2: {
        "markdown": """
### Valid matching brackets
Given a string `s` of brackets that can either be `[]`, `()` or `{}`.
Check if the brackets are valid.

There no other characters in the string apart from '[', ']', '(', ')', '{'and '}'.

### Example
```
s = "[](){}"
output = True

s = "{{}}[][](()"
output = False
```
""",
        "test_cases": """
test_cases = [
    [is_valid("[](){}"), True],
    [is_valid("{{}}[][](()"), False],
    [is_valid("[[[()]]]{}"), True],
    [is_valid("[[[(((((((()))))))]]]{[{[{[{{({})}}]}]}]}"), False],
    [is_valid("[[[([[[[[[[[[[[[[[[()]]]]]]]]]]]]]]])]]]{}"), True],
    [is_valid("[[[()]]]{[](){}()[{[{{]}}]}]}"), False],
    [is_valid("[[[()]]]{[](){}()[{[{{[]]}}]}]}{}[]((()))"), False],
    [is_valid("[[[()]]]{}"), True],
    [is_valid("["), False],
    [is_valid("{}" * 50_000 + "()" * 50_000 + "[]"), True],
    [is_valid("{{{{{{{{{{{{{{{{{{{{{{{{{{{{[[[[[[[[[[()]]]]]]]]]]}}}}}}}}}}}}}}}}}}}}}}}}}}}}"), True],
    [is_valid("[" + "()" * 100_000 + ")"), False],
    [is_valid("[" + "()" * 100_000 + "]"), True],
]
""",
        "title": "Valid matching brackets",
        "level": "Breezy",
        "code": """def is_valid(s: str) -> bool:
""",
    },
    3: {
        "markdown": """
### Max sum sub array
Given a non empty integer array `nums`, find a contiguous non-empty subarray within the array that has the largest sum and return the sum.

### Example
```
nums = [-2, 0, -1]
output = 0

nums = [2, 3, -2, 4]
output = 7
```
```
""",
        "test_cases": """
test_cases = [
    [max_sum([-2, 0, -1]), 0],
    [max_sum([-2, 0, -1] * 1000), 0],
    [max_sum([2, 3, -2, 4]), 7],
    [max_sum([2, 3, -2, 4] * 100_000), 700_000],
    [max_sum([-2]), -2],
    [max_sum([i for i in range(100_000)]), 4_999_950_000],
    [max_sum([2] * 50_000 + [-2] * 50_000), 100_000],
    [max_sum([2, -4, 8, 6, 9, -1, 3, -4, 12]), 33],
    [max_sum([2, -4, 8, 0, 9, -1, 0, -4, 12]), 24],
    [max_sum([2, -4, 8, 0, 9, -1, 0, -4, 12] * 10_000), 220_002],
]
""",
        "title": "Max sum sub array",
        "level": "Breezy",
        "code": """def max_sum(nums: list[int]) -> int:
""",
    },
    4: {
        "markdown": """
### Max product sub array
Given a non empty integer array `nums`, find a contiguous non-empty subarray within the array that has the largest product and return the product.

### Example
```
nums = [-2, 0, -1]
output = 0

nums = [2, 3, -2, 4]
output = 6
```
```
""",
        "test_cases": """
test_cases = [
    [max_product([-2, 0, -1]), 0],
    [max_product([2, 3, -2, 4]), 6],
    [max_product([-2, 0, -1, -3]), 3],
    [max_product([-2]), -2],
    [max_product([1 for _ in range(200_000)]), 1],
    [max_product([2, -4, 8, 6, 9, -1, 3, -4, 12]), 497664],
    [max_product([2, 0, 0, 0, 0, 0, 0, 0, 12]), 12],
    [max_product([2, -4, 1, -6, 0, -1, 3, 0, 12]), 48],
    [max_product([2, -4, 8, 0, 9, -1, 3, -4, 0]), 12],
    [max_product([2, -4, 0, 6, 9, 0, 3, -4, 12]), 54],
    [max_product([2, 0, 8, 6, 9, 0, 3, 0, 12]), 432],
    [max_product([1, -1, 1, 1, 1, -1, 1, -1, 1]), 1],
    [max_product([2, -1, -1, 1, 1, -1, 0, 2, 1]), 2],
    [max_product([2, -1, -1, 1, 1, -1, 0, 2, 1] * 100_000), 4],
]
""",
        "title": "Max product sub array",
        "level": "Steady",
        "code": """def max_product(nums: list[int]) -> int:
""",
    },
    5: {
        "markdown": """
### Symmetric difference
Create a function that takes two or more `arrays` and returns a `set` of their symmetric difference.

> The mathematical term symmetric difference (△ or ⊕) of two sets is the set of elements which are in either of the two sets but not in both.

### Example
```
arrays = [1, 2, 3], [2, 3, 4]
output = {1, 4}
```
""",
        "test_cases": """
test_cases = [
    [symmetric_difference([1, 2, 3], [2, 3, 4]), {1, 4}],
    [symmetric_difference([1, 2, 3, 3, 2]), {1, 2, 3}],
    [symmetric_difference([1], [2], [3], [4], [5], [6]), {1, 2, 3, 4, 5, 6}],
    [symmetric_difference([1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7]), {1, 7}],
    [symmetric_difference([1, 2, 4, 4], [0, 1, 6], [0, 1]), {2, 4, 6}],
    [symmetric_difference([0], [1], [2], [3], [4], [5]), {0, 1, 2, 3, 4, 5}],
    [symmetric_difference([-1], [], [], [0], [1]), {-1, 0, 1}],
    [symmetric_difference([9, -4, 8, 3, 12, 0, -4, 8], [3, 3, 8, 6, 7, 10], [11, 12, 10, 13], [5, 15, 3], [11, 15, 11, 11, 6, -2]), {9, -4, 0, 7, 13, 5, -2}],
    [symmetric_difference([2] * 50_000 + [-2] * 50_000), {2, -2}],
    [symmetric_difference([i for i in range(100_000)], [i for i in range(100_000)]), set()],
    [symmetric_difference([i for i in range(100_000)], [i for i in range(10, 100_000)]), {i for i in range(10)}],
]
""",
        "title": "Symmetric difference",
        "level": "Breezy",
        "code": """def symmetric_difference(*arrs):

""",
    },
    6: {
        "markdown": """
### Pairwise
Given an array `arr`, find element pairs whose sum equal the second argument `target` and return the sum of their indices.

Each element can only construct a single pair.

### Example
```
arr = [7, 9, 11, 13, 15]
target = 20
output = 6
How: pairs 7 + 13 and 9 + 11, indices 0 + 3 and 1 + 2, total 6

arr = [0, 0, 0, 0, 1, 1]
target = 1
output = 10
How: pairs 0 + 1 and 0 + 1, indices 0 + 4 and 1 + 5, total 10
```
""",
        "test_cases": """
test_cases = [
    [pairwise([7, 9, 11, 13, 15], 20), 6],
    [pairwise([0, 0, 0, 0, 1, 1], 1), 10],
    [pairwise([-1, 6, 3, 2, 4, 1, 3, 3], 5), 15],
    [pairwise([1, 6, 5], 6), 2],
    [pairwise([1, 6, 5, 15, 13, 2, 11], 10), 0],
    [pairwise([i for i in range(0, 100_000, 10)], 10), 1],
]
""",
        "title": "Pairwise",
        "level": "Breezy",
        "code": """def pairwise(arr: list[int], target: int) -> int:
""",
    },
    7: {
        "markdown": """
### Min length sub array
Given an array of positive integers `nums` and a positive integer `target`, return the minimal length of a subarray whose sum is greater than or equal to target.

If there is no such subarray, return `0` instead.

### Example
```
nums = [2, 3, 1, 2, 4, 3]
target = 7
output = 2
How: sub array [4, 3] has sum >= 7

nums = [1, 3, 6, 2, 1]
target = 4
output = 1
How: sub array [6] has sum >= 4
```
""",
        "test_cases": """
test_cases = [
    [min_len_arr([2, 3, 1, 2, 4, 3], 7), 2],
    [min_len_arr([1, 3, 6, 2, 1], 4), 1],
    [min_len_arr([i for i in range(500_000)], 3_000_000), 7],
    [min_len_arr([i for i in range(100)], 60), 1],
    [min_len_arr([i for i in range(100_000)], 60_000_000), 602],
    [min_len_arr([i for i in range(1_000_000)], 60_000_000), 61],
]
""",
        "title": "Min length sub array",
        "level": "Steady",
        "code": """def min_len_arr(arr: list[int], target: int) -> int:
""",
    },
    8: {
        "markdown": """
### Min in rotated array
Given a sorted (ascending order) but rotated array `nums`, return the minimum element of this array. You must write an algorithm that runs in **O(log n)** time. 

> an example of rotating an array. If `[0, 1, 2, 4, 5, 6, 7]` is rotated 4 times it becomes `[4, 5, 6, 7, 0, 1, 2]`.

### Example
```
arr = [4, 5, 6, 7, 0, 1, 2]
output = 0
```
""",
        "test_cases": """
test_cases = [
    [rotated_min([4, 5, 6, 7, 0, 1, 2]), 0],
    [rotated_min([16, 23, 43, 55, -7, -4, 3, 5, 9, 15]), -7],
    [rotated_min([i for i in range(36, 1_000_000, 10)]), 36],
    [rotated_min([i for i in range(-10, 1_000_000, 10)] + [i for i in range(-1_000_000, -10, 10)]), -1_000_000],
    [rotated_min([2]), 2],
    [rotated_min([134, 140, 147, 156, 160, 164, 166, 166, 170, 183, 184, 192, -9, -4, 1, 20, 51, 54, 54, 56, 67, 75, 80, 88, 92, 93, 96, 105, 115, 127]), -9],
]
""",
        "title": "Min in rotated array",
        "level": "Steady",
        "code": """def rotated_min(arr: list[int]) -> int:
""",
    },
    9: {
        "markdown": """
### Count primes
Given a positive integer `n`, write an algorithm to return the number of prime numbers in `[0, n]`.

### Example
```
n = 1000
output = 168
How: There are 168 prime numbers between 0 and 1000 inclusive.
```
""",
        "test_cases": """
test_cases = [
    [count_primes(100), 25],
    [count_primes(1_000), 168],
    [count_primes(10_000), 1229],
    [count_primes(100_000), 9592],
    [count_primes(2), 1],
    [count_primes(3), 2],
    [count_primes(1), 0],
    [count_primes(1_000_000), 78498],
]
""",
        "title": "Count primes",
        "level": "Steady",
        "code": """def count_primes(n: int) -> int:
""",
    },
    10: {
        "markdown": """
### Single number
Given a non-empty array of integers `nums` where every element appears twice except for one. Return the element that appears once.

You must write an algorithm that runs in **O(n)** average time complexity and uses constant space.

### Example
```
nums = [4, 1, 2, 1, 2]
output = 4
```
""",
        "test_cases": """
test_cases =  [
    [single_num([4, 1, 2, 1, 2]), 4],
    [single_num([2]), 2],
    [single_num([i for i in range(1, 500_000)] + [i for i in range(500_000)]), 0],
    [single_num([i for i in range(500_000)] + [-2, -3] + [i for i in range(500_000)] + [-2]), -3],
    [single_num([i for i in range(1, 500_000)] * 2 + [-4]), -4],
    [single_num([500_001] + [i for i in range(-500, 000, 500_000)] * 2), 500_001],
]
""",
        "title": "Single number",
        "level": "Breezy",
        "code": """def single_num(arr: list[int]) -> int:
""",
    },
    11: {
        "markdown": """
### Powers of 2
Given an integer `n`, find whether it is a power of `2`.

### Example
```
n = 64
output = True

n = 20
output = False
```
""",
        "test_cases": """
test_cases = [
    [is_power(64), True],
    [is_power(20), False],
    [is_power(1024), True],
    [is_power(2), True],
    [is_power(0), False],
    [is_power(1267650600228229401496703205376), True],
    [is_power(1267650600228229401496703205377), False],
    [is_power(-64), False],
]
""",
        "title": "Powers of 2",
        "level": "Breezy",
        "code": """def is_power(n: int) -> bool:
""",
    },
    12: {
        "markdown": """
### Reverse Polish Notation
Evaluate the value of an arithmetic expression in Reverse Polish Notation. Valid operators are `+`, `-`, `*`, and `/`. Each operand may be an integer or another expression.

Division between two integers should truncate toward zero and it is guaranteed that the given RPN expression is always valid.

### Example
```
input: ["2", "1", "+", "3", "*"]
output = 9
How: ((2 + 1) * 3) = 9

input: ["4", "13", "5", "/", "+"]
output = 6
How: (4 + (13 / 5)) = 6
```
""",
        "test_cases": """
test_cases = [
    [rpn(["2", "1", "+", "3", "*"]), 9],
    [rpn(["4", "13", "5", "/", "+"]), 6],
    [rpn(["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]), 12],
    [rpn(["10", "6", "9", "3", "+", "-11", "/", "*", "*", "17", "+", "5", "+"]), -98],
    [rpn(['1'] + ['2', '+'] * 100_000), 200_001],
    [rpn(['2'] + ['1', '*'] * 100_000), 2],
]
""",
        "title": "Reverse polish notation",
        "level": "Breezy",
        "code": """def rpn(v: list[str]) -> int:
""",
    },
    13: {
        "markdown": """
### Roman numerals
Convert a given integer, `n`,  to its equivalent roman numerals for `0 < n < 4000`.

|Decimal | 1000 | 900 | 500 | 400 | 100 |90|
|--------|------|-----|-----|-----|----|---|
|Roman | M | CM | D | CD | C |XC|

|Decimal| 50| 40 | 10| 9 | 5 | 4 | 1 |
|-------|---|----|---|---|---|---|---|
|Roman  | L | XL | X | IX| V | IV| I|


### Example
```
input: 4
output = 'IV'

input: 23
output = 'XXIII'
```
""",
        "title": "Roman numerals",
        "level": "Steady",
        "code": """def int_to_roman(n: int) -> str:
""",
        "test_cases": """
test_cases = [
    [int_to_roman(4), "IV"],
    [int_to_roman(23), "XXIII"],
    [int_to_roman(768), "DCCLXVIII"],
    [int_to_roman(1), "I"],
    [int_to_roman(3999), "MMMCMXCIX"],
    [int_to_roman(369), "CCCLXIX"],
    [int_to_roman(1318), "MCCCXVIII"],
    [int_to_roman(1089), "MLXXXIX"],
    [int_to_roman(2424), "MMCDXXIV"],
    [int_to_roman(999), "CMXCIX"],
]
""",
    },
    14: {
        "markdown": """
### Longest common substring (LCS)
Given two strings `text1` and `text2`, return their longest common substring. If there is no common substring, return ''.

> A substring of a string is a new string generated from the original string with adjacent characters. For example, "rain" is a substring of "grain". 

### Example
```
input: text1 = "brain", text2 = 'drain'
output = 'rain'
```
""",
        "title": "Longest common substring",
        "level": "Steady",
        "code": """def lcs(text1: str, text2: str) -> str:
""",
        "test_cases": """
test_cases = [
    [lcs("brain", "drain"), "rain"],
    [lcs("math", "arithmetic"), "th"],
    [lcs("abca" * 360, "bca" * 500), "abca"],
    [lcs("abc" * 400, "xyz" * 300), ""],
    [lcs("blackmarket", "stagemarket"), "market"],
    [lcs("theoldmanoftheseaissowise", "sowisetheoldmanoftheseais"), "theoldmanoftheseais"],
]
""",
    },
    15: {
        "markdown": """
### Happy number
Given a positive integer `n`, return whether it is a happy number or not. 

> A happy number is a number which if you repeatedly sum the squares of its digits the process will eventually lead to 1. For example, 19 → `1²+9²=82` → `8²+2²=68` → `6²+8²=100` → `1`.
### Example
```
input: 19
output = True

input: 2
output = False
```
""",
        "title": "Happy number",
        "level": "Breezy",
        "code": """def is_happy(n: int) -> bool:
""",
        "test_cases": """
test_cases = [
    [is_happy(19), True],
    [is_happy(2), False],
    [is_happy(17), False],
    [is_happy(202), False],
    [is_happy(711), False],
    [is_happy(176), True],
    [is_happy(19_345_672), False],
    [is_happy(345_000_000), False],
    [is_happy(1_703_932), False],
    [is_happy(2_294_967_295), False],
    [is_happy(1), True],
]
""",
    },
    16: {
        "markdown": """
### Trie/Prefix tree
Given an array `roots` of strings and a `sentence` of words separated by spaces. Replace all the words in the sentence with the root forming it. If a word can be replaced by more than one root, replace it with the shortest length root. 

Return the sentence after the replacement.

### Example
```
input: roots = ["cat", "bat", "rat"], sentence = "the cattle was rattled by the battery"
output = "the cat was rat by the bat"

input: roots = ["a", "b", "c"], sentence = "aadsfasf absbs bbab cadsfafs"
output = "a a b c"
```
""",
        "title": "Trie/Prefix tree",
        "level": "Steady",
        "code": """def replace(roots: list[str], sentence: str) -> str:
""",
        "test_cases": """
test_cases = [
    [replace(["cat", "bat", "rat"], "the cattle was rattled by the battery"), "the cat was rat by the bat"],
    [replace(["a", "b", "c"], "aadsfasf absbs bbab cadsfafs"), "a a b c"],
    [replace(["a", "b", "c"], "aadsfasf absbs bbab cadsfafs " * 100_000), ("a a b c " * 100_000).rstrip()],
    [replace([c for c in 'aceghikmnprsuvwxyz'], "the quick brown fox jumped over the lazy dog"), "the quick brown fox jumped over the lazy dog"],
    [replace([c for c in 'abcdefghijklmnopqrstuvwxyz'], "the quick brown fox jumped over the lazy dog"), "t q b f j o t l d"],
    [replace([c for c in 'abcdefghijklmnopqrstuvwxyz'], ""), ""],
]
""",
    },
    17: {
        "markdown": """
### Fractional knapsack
Given a knapsack `capacity` and two arrays, the first one for `weights` and the second one for `values`. Add items to the knapsack to maximize the sum of the values of the items that can be added so that the sum of the weights is less than or equal to the knapsack capacity.

You are allowed to add a fraction of an item.

### Example
```
inputs: capacity = 50, weights = [10, 20, 30], values = [60, 100, 120]
output = 240
```
""",
        "title": "Fractional knapsack",
        "level": "Breezy",
        "code": """def knapsack(capacity: int, weights: list[int], values: list[int]) -> int:
""",
        "test_cases": """
test_cases = [
    [knapsack(50, [10, 20, 30], [60, 100, 120]), 240],
    [knapsack(60, [10, 20, 30], [60, 100, 120]), 280],
    [knapsack(9, [10, 20, 30], [60, 100, 120]), 54],
    [knapsack(0, [10, 20, 30], [60, 100, 120]), 0],
    [knapsack(9, [10, 20, 30], [60, 100, 120]), 54],
    [knapsack(5, [], []), 0],
    [knapsack(6000, [10, 20, 30], [60, 100, 120]), 280],
    [knapsack(5, [10, 20, 30] * 1000, [60, 100, 120] * 1000), 30],
    [knapsack(5000, [10, 20, 30] * 100_000, [60, 100, 120] * 100_000), 30_000],
]
""",
    },
    18: {
        "markdown": """
### Subarrays with sum
Given an array `arr` and `target`, return the total number of contigous subarrays inside the array whose sum is equal to `target`

### Example
```
inputs: arr = [13, -1, 8, 12, 3, 9], target = 12
output = 3
How: [13, -1], [12] and [3, 9]
```
""",
        "title": "Subarrays with sum",
        "level": "Steady",
        "code": """def count_arrs(arr: list[int], target: int) -> int:
""",
        "test_cases": """
test_cases = [
    [count_arrs([13, -1, 8, 12, 3, 9], 12), 3],
    [count_arrs([13, -1, 8, 12, 3, 9], 2), 0],
    [count_arrs([13, -1, 8, 12, 3, 9], 10), 0],
    [count_arrs([13, -1, 8, 12, 3, 9, 7, 5, 9, 10], 75), 1],
    [count_arrs([13, -1, 8, 12, 3, 9] * 20_000, 12), 60_000],
    [count_arrs([13, -1, 8, 12, 3, 9, 7, 5, 9, 10] * 10_000, 24), 30_000],
]
""",
    },
    19: {
        "markdown": """
### Paths with sum
Given the `root` of a binary tree and an integer `target`, return the number of paths where the sum of the values along the path equals `target`.

The path does not need to start or end at the root or a leaf, but it must go downwards (i.e., traveling only from parent nodes to child nodes).

### Example
```
inputs: root = [10, 5, -3, 3, 2, None, 11, 3, -2, None, 1], target = 8
output = 3
```
""",
        "test_cases": f"""
{binary_tree}
root1 = array_to_tree([10, 5, -3, 3, 2, None, 11, 3, -2, None, 1])
root2 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1])
root3 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1] * 100_000)
root4 = array_to_tree([])
root5 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
test_cases = [
        [count_paths(root1, 8), 3],
        [count_paths(root2, 22), 3],
        [count_paths(root2, 20), 1],
        [count_paths(root3, 20), 11311],
        [count_paths(root3, 22), 13557],
        [count_paths(root4, 0), 0],
        [count_paths(root5, 195), 1],
        [count_paths(root5, 1000), 1],
        [count_paths(root5, 40), 0],
]
""",
        "title": "Paths with sum",
        "level": "Steady",
        "code": """def count_paths(root, target):
""",
    },
    20: {
        "markdown": """
### Spinal case
Given a string `s`. Convert it to spinal case

> Spinal case is all-lowercase-words-joined-by-dashes.

### Example
```
input: "Hello World!"
output = "hello-world"
```
""",
        "title": "Spinal case",
        "level": "Steady",
        "code": """def spinal_case(s: str) -> str:
""",
        "test_cases": """
test_cases = [
    [spinal_case("Hello World!"), "hello-world"],
    [spinal_case("The Greatest of All Time."), "the-greatest-of-all-time"],
    [spinal_case("yes/no/trueFalse"), "yes-no-true-false"],
    [spinal_case("yes/no/trueFalse" * 60_000), "yes-no-true-false" * 60_000],
    [spinal_case("follow-this-link"), "follow-this-link"],
    [spinal_case(""), ""],
    [spinal_case("...I-am_here lookingFor  You.See!!"), "i-am-here-looking-for-you-see"],
]
""",
    },
    21: {
        "markdown": """
### 0/1 knapsack
Given a knapsack `capacity` and two arrays, the first one for `weights` and the second one for `values`. Add items to the knapsack to maximize the sum of the values of the items that can be added so that the sum of the weights is less than or equal to the knapsack capacity.

You can only either include or not include an item. i.e you can't add a portion of it.

Return a tuple of maximum value and selected items

### Example
```
input: capacity = 50, weights = [10, 20, 30], values = [60, 100, 120]
output = (220, [0, 1, 1])
```
""",
        "title": "0/1 knapsack",
        "level": "Steady",
        "code": """def knapsack(capacity: int, weights: list[int], values: list[int]) -> tuple[int, list[int]]:
""",
        "test_cases": """
test_cases = [
    [knapsack(50, [10, 20, 30], [60, 100, 120]), (220, [0, 1, 1])],
    [knapsack(60, [10, 20, 30], [60, 100, 120]), (280, [1, 1, 1])],
    [knapsack(9, [10, 20, 30], [60, 100, 120]), (0, [0, 0, 0])],
    [knapsack(0, [10, 20, 30], [60, 100, 120]), (0, [0, 0, 0])],
    [knapsack(5, [], []), (0, [])],
    [knapsack(5, [10, 20, 30] * 100, [60, 100, 120] * 100), (0, [0] * 300)],
    [knapsack(10, [10, 20, 30] * 10_000, [60, 100, 120] * 10_000), (60, [1] + [0] * 29999)],
]
""",
    },
    22: {
        "markdown": """
### Equal array partitions
Given an integer array `nums`, return true if you can partition the array into two subsets such that the sum of the elements in both subsets is equal or false otherwise.

### Example
```
input: [1, 5, 11, 5]
output = True
How: [1, 5, 5] and [11]
```
""",
        "title": "Equal array partitions",
        "level": "Steady",
        "code": """def can_partition(nums: list[int]) -> bool:
""",
        "test_cases": """
test_cases = [
    [can_partition([1, 5, 11, 5]), True],
    [can_partition([6]), False],
    [can_partition([i for i in range(300)]), True],
    [can_partition([1, 5, 13, 5]), False],
    [can_partition([1, 5, 11, 5] * 100), True],
    [can_partition([1, 5, 13, 5, 35, 92, 11, 17, 13, 53]), False],
    [can_partition([i for i in range(1, 330, 2)]), False],
]
""",
    },
    23: {
        "markdown": """
### Climb stairs
You are climbing a staircase. It takes `n` steps to reach the top. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?

### Example
```
input: 0
output = 0
How: no stairs, no way to get to the top

input: 1
output = 1
How: 1 stair, one way to get to the top

input: 2
output = 2
How:
  2 ways to get to the top
    - climb stair 1 then stair 2
    - climb 2 steps to stair 2
```
""",
        "title": "Climb stairs",
        "level": "Breezy",
        "code": """def climb_stairs(n: int) -> int:
""",
        "test_cases": """
test_cases = [
    [climb_stairs(0), 0],
    [climb_stairs(1), 1],
    [climb_stairs(2), 2],
    [climb_stairs(10), 89],
    [climb_stairs(51), 32951280099],
    [climb_stairs(500), 225591516161936330872512695036072072046011324913758190588638866418474627738686883405015987052796968498626],
]
""",
    },
    24: {
        "markdown": """
### Ways to make change
Write an algorithm to determine how many ways there are to make change for a given input, `cents` of US currency. 

There are four types of common coins in US currency:
  - quarters (25 cents)
  - dimes (10 cents)
  - nickels (5 cents)
  - pennies (1 cent)

### Example
```
input: 15
output = 6
How: There are six ways to make change for 15 cents
  - A dime and a nickel
  - A dime and 5 pennies
  - 3 nickels
  - 2 nickels and 5 pennies
  - A nickel and 10 pennies
  - 15 pennies

```
""",
        "title": "Ways to make change",
        "level": "Steady",
        "code": """def count_ways(cents: int) -> int:
""",
        "test_cases": """
test_cases = [
    [count_ways(10), 4],
    [count_ways(15), 6],
    [count_ways(5), 2],
    [count_ways(55), 60],
    [count_ways(1000), 142511],
    [count_ways(10_000), 134235101],
]
""",
    },
    25: {
        "markdown": """
### Has path sum
Given the `root` of a binary tree and an integer `target`, return true if the tree has a root-to-leaf path such that adding up all the values along the path equals `target`.

> A leaf is a node with no children.

### Example
```
input: root = [5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, None, None, 1], target = 18
output = True
```
""",
        "test_cases": f"""
{binary_tree}
root1 = array_to_tree([10, 5, -3, 3, 2, None, 11, 3, -2, None, 1])
root2 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1])
root3 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1] * 100_000)
root4 = array_to_tree([])
root5 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, None, None, 1])
# bst
root6 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
root7 = sorted_to_bst([i for i in range(100)])
root8 = sorted_to_bst([i for i in range(-100_000, 100_000)])
test_cases = [
    [has_path_sum(root1, 18), True],
    [has_path_sum(root2, 18), False],
    [has_path_sum(root3, 182), True],
    [has_path_sum(root3, 44), False],
    [has_path_sum(root3, 43), True],
    [has_path_sum(root4, 0), False],
    [has_path_sum(root5, 26), True],
    [has_path_sum(root6, 1000), False],
    [has_path_sum(root6, 205), True],
    [has_path_sum(root7, 577), True],
    [has_path_sum(root7, 411), False],
    [has_path_sum(root8, -99996), True],
]
""",
        "title": "Has path sum",
        "level": "Steady",
        "code": """def has_path_sum(root, target):
""",
    },
    26: {
        "markdown": """
### Has node BST
Given the `root` of a binary search tree and a value `x`, check whether x is in the tree and return `True` or `False`

### Example
```
input: root = [9, 8, 16], x = 5
output = False

input: root = [12, 3, 20], x = 3
output = True
```
""",
        "test_cases": f"""
{binary_tree}
root1 = array_to_tree([9, 8, 16])
root2 = array_to_tree([9, 8, 16, 4])
root3 = array_to_tree([12, 3, 20, None, 5])
root5 = array_to_tree([])
root6 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
root7 = sorted_to_bst([i for i in range(100)])
root8 = sorted_to_bst([i for i in range(-100_000, 100_000)])
test_cases = [
    [has_node_bst(root1, 5), False],
    [has_node_bst(root2, 9), True],
    [has_node_bst(root3, 5), True],
    [has_node_bst(root5, 4), False],
    [has_node_bst(root6, 600), True],
    [has_node_bst(root7, 100), False],
    [has_node_bst(root8, 1), True],
]
""",
        "title": "Has node BST",
        "level": "Steady",
        "code": """def has_node_bst(root, x):
""",
    },
    27: {
        "markdown": """
### BST min
Given the `root` of a binary search tree find the minimum value and return it

### Example
```
input: [12, 3, 20]
output = 3
```
""",
        "test_cases": f"""
{binary_tree}
root1 = array_to_tree([9, 8, 16])
root2 = array_to_tree([9, 8, 16, 4])
root3 = array_to_tree([12, 3, 20, None, 5])
root6 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
root7 = sorted_to_bst([i for i in range(100)])
root8 = sorted_to_bst([i for i in range(-100_000, 100_000)])
test_cases = [
    [min_bst(root1), 8],
    [min_bst(root2), 4],
    [min_bst(root3), 3],
    [min_bst(root6), 45],
    [min_bst(root7), 0],
    [min_bst(root8), -100_000],
]
""",
        "title": "BST min",
        "level": "Steady",
        "code": """def min_bst(root):
""",
    },
    28: {
        "markdown": """
### Balanced tree
Given the `root` of a binary tree, return `True` if it is balanced or `False` otherwise

> A balanced tree is one whose difference between maximum height and minimum height is less than 2

### Example
```
input: [12, 8, 16, 4, 9, 13, 18, 11]
output = True

input: [4, None, 9, None, None, None, 12]
output = False
```
""",
        "test_cases": f"""
{binary_tree}
root1 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1])
root2 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1] * 100_000)
root3 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, None, None, 1])
# bst
root4 = array_to_tree([9, 8, 16])
root5 = array_to_tree([9, 8, 16, 4])
root6 = array_to_tree([12, 3, 20, None, 5])
root7 = array_to_tree([])
root8 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
root9 = sorted_to_bst([i for i in range(100)])
root10 = sorted_to_bst([i for i in range(-100_000, 100_000)])
test_cases = [
    [is_balanced(root1), False],
    [is_balanced(root2), False],
    [is_balanced(root3), False],
    [is_balanced(root4), True],
    [is_balanced(root5), True],
    [is_balanced(root6), True],
    [is_balanced(root7), True],
    [is_balanced(root8), True],
    [is_balanced(root9), True],
    [is_balanced(root10), True],
]
""",
        "title": "Balanced tree",
        "level": "Steady",
        "code": """def is_balanced(root):
""",
    },
    29: {
        "markdown": """
### Tree in-order traversal
Given the `root` of a binary tree, traverse the tree in order and return the values as an array.

### Example
```
input: [12, 8, 16, 4, 9, 13, 18, 1]
output = [1, 4, 8, 9, 12, 13, 16, 18]
```
""",
        "test_cases": f"""
{binary_tree}
root3 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, None, None, 1])
# bst
root4 = array_to_tree([9, 8, 16])
root5 = array_to_tree([12, 8, 16, 4, 9, 13, 18, 1])
root6 = array_to_tree([12, 3, 20, None, 5])
root7 = array_to_tree([])
root8 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
root9 = sorted_to_bst([i for i in range(100)])
root10 = sorted_to_bst([i for i in range(-100_000, 100_000)])
test_cases = [
    [in_order(root3), [7, 11, 2, 4, 5, 13, 8, 4, 1]],
    [in_order(root4), [8, 9, 16]],
    [in_order(root5), [1, 4, 8, 9, 12, 13, 16, 18]],
    [in_order(root6), [3, 5, 12, 20]],
    [in_order(root7), []],
    [in_order(root8), [45, 50, 55, 100, 500, 600, 1000]],
    [in_order(root9), [i for i in range(100)]],
    [in_order(root10), [i for i in range(-100_000, 100_000)]],
]
""",
        "title": "Tree in-order traversal",
        "level": "Steady",
        "code": """def in_order(root):
""",
    },
    30: {
        "markdown": """
### Valid BST
Given the `root` of a binary tree, check whether it is a valid binary search tree.

> **Valid BST:** for every node, all nodes in its left subtree are less than the node value and all nodes in its right subtree are greater than the node value. 

### Example
```
input: [9, 8, 16]
output = true
```
""",
        "test_cases": f"""
{binary_tree}
root1 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1])
root2 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1] * 100_000)
root3 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, None, None, 1])
# bst
root4 = array_to_tree([9, 8, 16])
root5 = array_to_tree([12, 8, 16, 4, 9, 13, 18, 1])
root6 = array_to_tree([12, 3, 20, None, 5])
root7 = array_to_tree([12, 8, 16, 4, 9, 13, 18, 11])
root8 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
root9 = sorted_to_bst([i for i in range(100)])
root10 = sorted_to_bst([i for i in range(-100_000, 100_000)])
test_cases = [
    [valid_bst(root1), False],
    [valid_bst(root2), False],
    [valid_bst(root3), False],
    [valid_bst(root4), True],
    [valid_bst(root5), True],
    [valid_bst(root6), True],
    [valid_bst(root7), False],
    [valid_bst(root8), True],
    [valid_bst(root9), True],
    [valid_bst(root10), True],
]
""",
        "title": "Valid BST",
        "level": "Steady",
        "code": """def valid_bst(root):
""",
    },
    31: {
        "markdown": """
### Tree level-order traversal
Given the `root` of a binary tree, traverse the tree using level order traversal and return the values as an array.

### Example
```
input: [12, 8, 16, 4, 9, 13, 18, 1]
output = [12, 8, 16, 4, 9, 13, 18, 1]
```
""",
        "test_cases": f"""
{binary_tree}
root3 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, None, None, 1])
# bst
root4 = array_to_tree([9, 8, 16])
root5 = array_to_tree([12, 8, 16, 4, 9, 13, 18, 1])
root6 = array_to_tree([12, 3, 20, None, 5])
root7 = array_to_tree([])
root8 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
root9 = sorted_to_bst([i for i in range(100)])
test_cases = [
    [level_order(root3), [5, 4, 8, 11, 13, 4, 7, 2, 1]],
    [level_order(root4), [9, 8, 16]],
    [level_order(root5), [12, 8, 16, 4, 9, 13, 18, 1]],
    [level_order(root6), [12, 3, 20, 5]],
    [level_order(root7), []],
    [level_order(root8), [100, 50, 600, 45, 55, 500, 1000]],
    [level_order(root9), [50, 25, 75, 12, 38, 63, 88, 6, 19, 32, 44, 57, 69, 82, 94, 3, 9, 16, 22, 29, 35, 41, 47, 54, 60, 66, 72, 79, 85, 91, 97, 1, 5, 8, 11, 14, 18, 21, 24, 27, 31, 34, 37, 40, 43, 46, 49, 52, 56, 59, 62, 65, 68, 71, 74, 77, 81, 84, 87, 90, 93, 96, 99, 0, 2, 4, 7, 10, 13, 15, 17, 20, 23, 26, 28, 30, 33, 36, 39, 42, 45, 48, 51, 53, 55, 58, 61, 64, 67, 70, 73, 76, 78, 80, 83, 86, 89, 92, 95, 98]],
]
""",
        "title": "Tree level-order traversal",
        "level": "Steady",
        "code": """def level_order(root):
""",
    },
    32: {
        "markdown": """
### Tree leaves
Given the `root` of a binary tree, return all the leaves as an array ordered from left to right.

> A leaf is tree node with no children. 

### Example
```
input: [100, 50, 600, 45, 55, 500, 1000]
output = [45, 55, 500, 1000]
```
""",
        "test_cases": f"""
{binary_tree}
root3 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, None, None, 1])
# bst
root4 = array_to_tree([9, 8, 16])
root5 = array_to_tree([12, 8, 16, 4, 9, 13, 18, 1])
root6 = array_to_tree([12, 3, 20, None, 5])
root7 = array_to_tree([])
root8 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
root9 = sorted_to_bst([i for i in range(100)])
test_cases = [
    [get_leaves(root3), [7, 2, 13, 1]],
    [get_leaves(root4), [8, 16]],
    [get_leaves(root5), [1, 9, 13, 18]],
    [get_leaves(root6), [5, 20]],
    [get_leaves(root7), []],
    [get_leaves(root8), [45, 55, 500, 1000]],
    [get_leaves(root9), [0, 2, 4, 7, 10, 13, 15, 17, 20, 23, 26, 28, 30, 33, 36, 39, 42, 45, 48, 51, 53, 55, 58, 61, 64, 67, 70, 73, 76, 78, 80, 83, 86, 89, 92, 95, 98]],
]
""",
        "title": "Tree leaves",
        "level": "Steady",
        "code": """def get_leaves(root):
""",
    },
    33: {
        "markdown": """
### Sum right nodes
Given the `root` of a binary tree, return the sum of all the right nodes

### Example
```
input: [12, 8, 16, 4, 9, 13, 18, 11]
output = 25
```
""",
        "test_cases": f"""
{binary_tree}
root1 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1])
root2 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1] * 100_000)
root3 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, None, None, 1])
# bst
root4 = array_to_tree([9, 8, 16])
root5 = array_to_tree([12, 8, 16, 4, 9, 13, 18, 1])
root6 = array_to_tree([12, 3, 20, None, 5])
root7 = array_to_tree([])
root8 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
root9 = sorted_to_bst([i for i in range(100)])
root10 = sorted_to_bst([i for i in range(-100_000, 100_000)])
test_cases = [
    [sum_right(root1), 15],
    [sum_right(root2), 211629],
    [sum_right(root3), 15],
    [sum_right(root4), 16],
    [sum_right(root5), 43],
    [sum_right(root6), 25],
    [sum_right(root7), 0],
    [sum_right(root8), 1655],
    [sum_right(root9), 1868],
    [sum_right(root10), 539765],
]
""",
        "title": "Sum right nodes",
        "level": "Steady",
        "code": """def sum_right(root):
""",
    },
    34: {
        "markdown": """
### Value in array
Given an array of integers `arr` sorted in a non decreasing order, and a target `y`. Return `True` if y is in the array or `False` otherwise

You must write an algorithm that runs in **O(log n)** average time complexity. 

### Example
```
input: arr = [2, 4, 8, 9, 12, 13, 16, 18], y = 18
output = True
```
""",
        "test_cases": """
test_cases = [
    [has_value([2, 4, 8, 9, 12, 13, 16, 18], 18), True],
    [has_value([i for i in range(5_000_000)], 45), True],
    [has_value([i for i in range(5_000_000)], 5_000_000), False],
    [has_value([i for i in range(-1_000_000, 1_000_000)], 0), True],
    [has_value([i for i in range(-1_000_000, 1_000_000)], -223), True],
    [has_value([i for i in range(-1_000_000, 1_000_000, 10)], 33), False],
]
""",
        "title": "Value in array",
        "level": "Breezy",
        "code": """def has_value(arr: list[int], target: int) -> bool:
""",
    },
    35: {
        "markdown": """
### Merge sort
Given an array of integers `nums`, use merge sort algorithm to return an array of all the integers sorted in non decreasing order.

### Example
```
input: [8, 2, 4, 9, 12, 18, 16, 13]
output = [2, 4, 8, 9, 12, 13, 16, 18]
```
""",
        "test_cases": """
from random import shuffle
nums = [i for i in range(-50_000, 60_000)]
shuffle(nums)
test_cases = [
    [merge_sort([8, 2, 4, 9, 12, 18, 16, 13]), [2, 4, 8, 9, 12, 13, 16, 18]],
    [merge_sort([i for i in range(100_000, -1, -1)]), [i for i in range(100_001)]],
    [merge_sort([i for i in range(10_000)]), [i for i in range(10_000)]],
    [merge_sort([8, 1, 5] * 100_000), [1] * 100_000 + [5] * 100_000 + [8] * 100_000],
    [merge_sort([3]), [3]],
    [merge_sort(nums), [i for i in range(-50_000, 60_000)]]
]
""",
        "title": "Merge sort",
        "level": "Breezy",
        "code": """def merge_sort(nums: list[int]) -> list[int]:
""",
    },
    36: {
        "markdown": """
### Heap sort
Given an array of integers `nums`, use heap sort algorithm to return an array of all the integers sorted in non decreasing order.

### Example
```
input: [8, 2, 4, 9, 12, 18, 16, 13]
output = [2, 4, 8, 9, 12, 13, 16, 18]
```
""",
        "test_cases": """
from random import shuffle
nums = [i for i in range(-50_000, 60_000)]
shuffle(nums)
test_cases = [
    [heap_sort([8, 2, 4, 9, 12, 18, 16, 13]), [2, 4, 8, 9, 12, 13, 16, 18]],
    [heap_sort([i for i in range(100_000, -1, -1)]), [i for i in range(100_001)]],
    [heap_sort([i for i in range(10_000)]), [i for i in range(10_000)]],
    [heap_sort([8, 1, 5] * 100_000), [1] * 100_000 + [5] * 100_000 + [8] * 100_000],
    [heap_sort([3]), [3]],
    [heap_sort(nums), [i for i in range(-50_000, 60_000)]]
]
""",
        "title": "Heap sort",
        "level": "Steady",
        "code": """def heap_sort(nums: list[int]) -> list[int]:
""",
    },
    37: {
        "markdown": """
### Generate parentheses
Given a positive integer `n`, generate all combinations of well formed parentheses with n pairs. 

### Example
```
input: n = 3
output = ["((()))","(()())","(())()","()(())","()()()"]

input: n = 1
output = ["()"]
```
""",
        "test_cases": """
def GENERATE_PARENTHESES(n: int) -> list[str]:
    res, path = [], []

    def backtrack(open: int, close: int) -> None:
        if len(path) == 2 * n:
            res.append(''.join(path))
            return 
        if open < n: 
            path.append('(')
            backtrack(open + 1, close)
            path.pop()
        if close < open:
            path.append(')')
            backtrack(open, close + 1)
            path.pop()
    
    backtrack(0, 0)
    return res 

test_cases = [
    [generate_parentheses(3), GENERATE_PARENTHESES(3)],
    [generate_parentheses(1), GENERATE_PARENTHESES(1)],
    [generate_parentheses(2), GENERATE_PARENTHESES(2)],
    [generate_parentheses(0), GENERATE_PARENTHESES(0)],
    [generate_parentheses(12), GENERATE_PARENTHESES(12)],
    [generate_parentheses(5), GENERATE_PARENTHESES(5)],
]
""",
        "title": "Generate parentheses",
        "level": "Steady",
        "code": """def generate_parentheses(n: int) -> list[str]:
""",
    },
    38: {
        "markdown": """
### Minimum connection cost
You are given `n` cities numbered from 1 to n and an array `connections` where connections[i] = [x, y, cost] indicates a weighted bidirectional connection between cities x and y. 

Return the minimum cost to connect all the n cities such that there is at least one path between each pair of cities. 

> The cost is the sum of the connections’ costs used.

Return -1 if it isn't possible to connect all n cities. 

### Example
```
n = 3
connections = [
        [1, 2, 10],
        [1, 2, 1],
        [2, 3, 2],
]
output = 3
```
""",
        "title": "Minimum connection cost",
        "level": "Steady",
        "code": """def minimum_cost(n: int, connections: list[list[int]]) -> int:
""",
        "test_cases": """
# Trivial / edge cases
g1_n = 1
g1 = []

g2_n = 2
g2 = [[1, 2, 10]]

g3_n = 2
g3 = []

# Disconnected
g4_n = 4
g4 = [
    [1, 2, 3],
    [2, 3, 4],
]

# Multiple edges between same cities
g5_n = 3
g5 = [
    [1, 2, 10],
    [1, 2, 1],
    [2, 3, 2],
]

# Simple cycle
g6_n = 4
g6 = [
    [1, 2, 1],
    [2, 3, 1],
    [3, 4, 1],
    [4, 1, 10],
]

# Dense cyclic graph
g7_n = 4
g7 = [
    [1, 2, 5],
    [1, 3, 6],
    [1, 4, 4],
    [2, 3, 2],
    [2, 4, 3],
    [3, 4, 1],
]

# Negative weights
g8_n = 3
g8 = [
    [1, 2, -5],
    [2, 3, 2],
    [1, 3, 10],
]

# Star topology
g9_n = 5
g9 = [
    [1, 2, 1],
    [1, 3, 1],
    [1, 4, 1],
    [1, 5, 1],
]

# Linear chain
g10_n = 6
g10 = [
    [1, 2, 1],
    [2, 3, 1],
    [3, 4, 1],
    [4, 5, 1],
    [5, 6, 1],
]

# Greedy trap
g11_n = 4
g11 = [
    [1, 2, 1],
    [2, 3, 100],
    [1, 3, 2],
    [3, 4, 1],
]

test_cases = [
    [minimum_cost(g1_n, g1), 0],
    [minimum_cost(g2_n, g2), 10],
    [minimum_cost(g3_n, g3), -1],
    [minimum_cost(g4_n, g4), -1],
    [minimum_cost(g5_n, g5), 3],
    [minimum_cost(g6_n, g6), 3],
    [minimum_cost(g7_n, g7), 7],
    [minimum_cost(g8_n, g8), -3],
    [minimum_cost(g9_n, g9), 4],
    [minimum_cost(g10_n, g10), 5],
    [minimum_cost(g11_n, g11), 4],
]
""",
    },
    39: {
        "markdown": """
### Smaller to the right
Given an integer array `nums`, return an integer array counts where counts[i] is the number of smaller elements to the right of nums[i].

### Example
```
input: [5, 2, 2, 6, 1]
output = [3, 1, 1, 1, 0]
```
""",
        "test_cases": """
test_cases = [
    [count_smaller([5, 2, 2, 6, 1]), [3, 1, 1, 1, 0]],
    [count_smaller([0]), [0]],
    [count_smaller([]), []],
    [count_smaller([8, 2, 4, 9, 12, 18, 16]), [2, 0, 0, 0, 0, 1, 0]],
    [count_smaller([i for i in range(100_000)]), [0] * 100_000],
    [count_smaller([i for i in range(100_000, 0, -1)]), [i for i in range(99_999, -1, -1)]],
]
""",
        "title": "Smaller to the right",
        "level": "Edgy",
        "code": """def count_smaller(nums: list[int]) -> list[int]:
""",
    },
    40: {
        "markdown": """
### Majority element 
Given an array `nums` of size n, return the majority element.

> The majority element is the element that appears more than
⌊n / 2⌋ times.

The majority element is guaranteed to exist in the array. 

### Example
```
Input: [3, 2, 3]
output = 3
```
""",
        "test_cases": """
test_cases = [
    [majority([3, 2, 3]), 3],
    [majority([6] * 20), 6],
    [majority([9] * 21 + [7] * 20), 9],
    [majority([2]), 2],
    [majority([]), None],
    [majority([6] * 100_000 + [9] * 100_001), 9],
    [majority([-2, -2, -4, -2, -4, -4, -4]), -4],
]
""",
        "title": "Majority element",
        "level": "Breezy",
        "code": """def majority(nums: list[int]) -> int:
""",
    },
    41: {
        "markdown": """
### Max profit
Given an array `prices` where `prices[i]` is the price of a given stock on the ith day. Return the maximum profit that can be made by choosing a single day to buy and choosing a different day in the future to sell that stock. 

If you cannot achieve any profit, return 0.

### Example
```
Input: prices = [7,1,5,3,6,4]
output = 5
How: Buy on day 2 (price = 1) and sell on day 5 (price = 6), profit = 6-1 = 5.

Input: prices = [7,6,4,3,1]
output = 0
```
""",
        "test_cases": """
test_cases = [
    [max_profit([7, 1, 5, 3, 6, 4]), 5],
    [max_profit([7, 6, 4, 3, 1]), 0],
    [max_profit([0, 0, 0, 0]), 0],
    [max_profit([4] * 2_000 + [15] * 1_000), 11],
    [max_profit([90] * 10_000 + [50] * 20_000), 0],
    [max_profit([]), 0],
    [max_profit([i for i in range(1, 100_000)]), 99_998],
]
""",
        "title": "Max profit",
        "level": "Breezy",
        "code": """def max_profit(prices: list[int]) -> int:
""",
    },
    42: {
        "markdown": """
### Pair sum equal target
Find two numbers in an array `nums` that add up to a specific `target`. Return the indices `[i, j]` such that `nums[i] + nums[j] = target`. 

Each input has exactly one solution.

### Example
```
- Input: nums = [2, 7, 1, 15], target = 9
- output = [0, 1] (because 2 + 7 = 9)
```
""",
        "test_cases": """
test_cases = [
    [pair_sum([2, 7, 1, 15], 22), [1, 3]],
    [pair_sum([2, 4, 7, 14], 6), [0, 1]],
    [pair_sum([0, 1], 1), [0, 1]],
    [pair_sum([2, 4, 7, 14] + [40] * 10_000, 6), [0, 1]],
    [pair_sum([30] * 100_000 + [2, 4, 7, 14], 6), [100_000, 100_001]],
    [pair_sum([10] * 100_000 + [2, 4, 7, 14] + [20] * 100_000, 6), [100_000, 100_001]],
]
""",
        "title": "Pair sum equal target",
        "level": "Breezy",
        "code": """def pair_sum(nums: list[int], target: int) -> int:
""",
    },
    43: {
        "markdown": """
### Longest common subsequence (LCS) 
Given two strings `str1` and `str2`, both lowercase, return their longest common subsequence. 

> A subsequence of a string is generated by selecting some characters from the original string while maintaining the relative order of the original characters. e.g 'man' is a subsequence of 'mountain'

### Example
```
Input: str1 = "mountain", str2 = "man"
output = 'man'

Input: str1 = "dent", str2 = "crab"
output = ''
```
""",
        "title": "Longest common subsequence",
        "level": "Steady",
        "code": """def lcs(str1: str, str2: str) -> str:
""",
        "test_cases": """
test_cases = [
    [lcs("math", "arithmetic"), "ath"],
    [lcs("original", "origin"), "origin"],
    [lcs("foo", "bar"), ""],
    [lcs("", "arithmetic"), ""],
    [lcs("shesellsseashellsattheseashore", "isawyouyesterday"), "saester"],
    [lcs("@work3r", "m@rxkd35rt"), "@rk3r"],
]
""",
    },
    44: {
        "markdown": """
### Can you reach the last index?
Given an integer array `nums` where `nums[i]` represents the maximum forward jump length from index `i`. Determine if, starting from the first index (0), you can reach the last index. 

### Example
```
Input: nums = [2,3,1,1,4]
output = true

Input: nums = [3,2,1,0,4]
output = false
```
""",
        "title": "Can you reach the last index?",
        "level": "Steady",
        "code": """def can_reach_end(nums: list[int]) -> bool:
""",
        "test_cases": """
test_cases = [
    [can_reach_end([2, 3, 1, 1, 4]), True],
    [can_reach_end([0]), True],
    [can_reach_end([2, 1, 1, 0, 4]), False],
    [can_reach_end([i for i in range(200_000)]), False],
    [can_reach_end([1 for _ in range(200_000)]), True],
    [can_reach_end([0, 0]), False],
    [can_reach_end([200_000] + [0] * 200_000), True],
]
""",
    },
    45: {
        "markdown": """
### Min jumps to reach last index
Given an integer array `nums` where `nums[i]` represents the maximum forward jump length from index `i`. Return the minimum jumps to get from the first index (0) to the last index. 

You are guaranteed to reach the last index. 

### Example
```
Input: nums = [2,5,2,1,4]
output = 2
How: jump 1 step to index 1 then 3 steps to the last index. 

Input: nums = [2,3,0,1,4,0]
output = 3
How: jump 1 step to index 1, 3 steps to index 4 then 1 step to the last index.
```
""",
        "title": "Min jumps to reach last index",
        "level": "Steady",
        "code": """def min_jumps(nums: list[int]) -> int:
""",
        "test_cases": """
test_cases = [
    [min_jumps([2, 3, 1, 1, 4]), 2],
    [min_jumps([1]), 0],
    [min_jumps([1, 5]), 1],
    [min_jumps([1 for _ in range(200_000)]), 199_999],
    [min_jumps([200_000] + [0] * 200_000), 1],
    [min_jumps([i for i in range(1, 100_000)]), 17],
]
""",
    },
    46: {
        "markdown": """
### Jump to zero
Given an integer array `nums` where `nums[i]` represents the maximum forward or backward jump length from index `i` and a starting index `start`. Check if you can jump to an index where the value is 0.

### Example
```
Input: nums = [4,2,3,0,3,1,2], start = 5
output = true
How: index 5 -> 4 -> 1 -> 3 or 5 -> 6 -> 4 -> 1 -> 3

Input: nums = [3,0,2,1,2], start = 2
output = false
How: There is no way to get to index 1 starting from index 2.
```
""",
        "title": "Jump to zero",
        "level": "Steady",
        "code": """def can_jump_to_zero(nums: list[int], start: int) -> bool:
""",
        "test_cases": """
test_cases = [
    [can_jump_to_zero([4, 2, 3, 0, 3, 1, 2], 0), True],
    [can_jump_to_zero([3, 0, 2, 1, 2], 2), False],
    [can_jump_to_zero([4, 2, 3, 0, 3, 1, 2], 5), True],
    [can_jump_to_zero([1] * 200_000 + [0], 567), True],
    [can_jump_to_zero([0], 0), True],
    [can_jump_to_zero([2, 4, 0, 1, 1, 1, 0, 2, 1], 8), True],
]
""",
    },
    47: {
        "markdown": """
### Max loot 
Given an integer array `nums` where each `nums[i]` represents the amount of cash stashed in a boat, return the maximum amount that you can steal from the boats given that you cannot steal from any two adjacent boats.  

### Example
```
Input: nums = [2,2,5,1]
output = 7
How: Rob boats 1 (2) and 3 (5) -> total loot 7 

Input: nums = [2]
output = 2
How:  Only one boat, no adjacent boats to worry about. 
```
""",
        "title": "Max loot",
        "level": "Steady",
        "code": """def max_loot(nums: list[int]) -> int:
""",
        "test_cases": """
test_cases = [
    [max_loot([1, 2, 3, 1]), 4],
    [max_loot([1, 7, 2, 1, 6]), 13],
    [max_loot([1, 2]), 2],
    [max_loot([3]), 3],
    [max_loot([133, 99, 17, 39, 54, 98, 57, 34, 23, 100]), 404],
    [max_loot([i for i in range(0, 100_000, 100)]), 25_000_000],
]
""",
    },
    48: {
        "markdown": """
### Max loot circle
Given an integer array `nums` where each `nums[i]` represents the amount of cash stashed in a boat, return the maximum amount that you can steal from the boats given that you cannot steal from any two adjacent boats and the boats are arranged in a circle i.e the last boat is adjacent to the first one. 

### Example
```
Input: nums = [3,5,3]
output = 5
How: Cannot rob boats 1 and 3 for total of 6 because they are adjacent. So rob boat 2. 
```
""",
        "title": "Max loot circle",
        "level": "Steady",
        "code": """def max_loot_circle(nums: list[int]) -> int:
""",
        "test_cases": """
test_cases = [
    [max_loot_circle([3, 5, 3]), 5],
    [max_loot_circle([1, 7, 2, 1, 6, 14]), 22],
    [max_loot_circle([3, 2, 5]), 5],
    [max_loot_circle([3]), 3],
    [max_loot_circle([133, 99, 17, 39, 54, 98, 57, 34, 23, 100]), 370],
    [max_loot_circle([i for i in range(0, 100_000, 100)]), 25_000_000],
]
""",
    },
    49: {
        "markdown": """
### Course schedule 
Given an array of `courses` representing the courses you have to take where courses[i] = [a, b] indicates that you must take course b in order to take course a. And an integer `n` representing the total number of courses with the courses being labelled from 0 to n - 1. Determine the order in which you can do all the courses. Return [] if you can't do all the courses. 

### Example
Input: n = 2, courses = [[1,0]]
output = [0, 1]
How: Take course 0 then 1. 

Input: n = 2, courses = [[1,0],[0,1]]
output = []
How: To take course 1 you first need to take course 0 but to take course 0 you need to first take course 1 so no way to take any of them. 
""",
        "title": "Course schedule",
        "level": "Steady",
        "code": """def course_schedule(n: int, courses: list[list[int]]) -> list[int]:
""",
        "test_cases": """
test_cases = [
    [course_schedule(2, [[1, 0], [0, 1]]), []],
    [course_schedule(4, [[1, 0], [2, 0], [3, 1], [3, 2]]), [0, 1, 2, 3]],
    [course_schedule(1, []), [0]],
    [course_schedule(10, [[0, 9]]), [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]],
    [course_schedule(10, [[0, 9], [8, 5]]), [1, 2, 3, 4, 5, 6, 7, 9, 8, 0]],
    [course_schedule(10, [[0, 9], [8, 5], [5, 8]]), []],
    [course_schedule(10, [[2, 3], [2, 4], [4, 3]]), [0, 1, 3, 5, 6, 7, 8, 9, 4, 2]],
]
""",
    },
    50: {
        "markdown": """
### Minimum height trees (MHTs) 
Given an integer `n` representing number of nodes in a tree and an array of `n-1` edges where edges[i] = [a, b] represent an undirected edge between nodes a and b. Return a list of minimum height trees root labels sorted in a non decreasing order. 

The nodes are labelled from 0 to n - 1. 

> A tree is an undirected graph in which any two vertices are connected by exactly one path. 

> The minimum height trees (MHTs) are nodes from a tree that if choosen as the root result to the minimum `height` of the tree. 

> The height of a tree is the number of edges on the path from the root to the the farthest leaf. 

### Example
```
Input: n = 4, edges = [[1,0],[1,2],[1,3]]
output = [1]

Input: n = 6, edges = [[3,0],[3,1],[3,2],[3,4],[5,4]]
output = [3,4]
```
""",
        "title": "Minimum height trees",
        "level": "Steady",
        "code": """def min_height(n: int, edges: list[list[int]]) -> list[int]:
""",
        "test_cases": """
test_cases = [
    [min_height(4, [[1, 0], [1, 2], [1, 3]]), [1]],
    [min_height(6, [[3, 0], [3, 1], [3, 2], [3, 4], [5, 4]]), [3, 4]],
    [min_height(10, [[6, 5], [6, 1], [1, 4], [1, 7], [3, 4], [7, 0], [4, 8], [7, 2], [2, 9]]), [1, 7]],
    [min_height(2, [[0, 1]]), [0, 1]],
    [min_height(100001, [[i, i + 1] for i in range(100_000)]), [50000]],
    [min_height(1000, [[i, i + 1] for i in range(999)]), [499, 500]],
]
""",
    },
    51: {
        "markdown": """
### Longest common prefix
Given an array of strings `strs` return the longest common prefix of all the strings. 

### Example
```
Input: strs = ["flower","flow","flight"]
output = "fl"

Input: strs = ["dog","racecar","car"]
output = ""
```
""",
        "title": "Longest common prefix",
        "level": "Steady",
        "code": """def longest_common_prefix(strs: list[str]) -> str:
""",
        "test_cases": """
test_cases = [
    [longest_common_prefix(["flower", "flow", "flight"]), "fl"],
    [longest_common_prefix(["dog", "racecar", "car"]), ""],
    [longest_common_prefix([ "algology", "algologies", "algologists", "algometer", "algometric", "algometry", "algophobia", "algologically", "algorithm", "algorism"]), "algo"],
    [longest_common_prefix(["ORGANOMETALLICS", "ORGANOPHOSPHATE", "ORGANOTHERAPY "]), "ORGANO"],
    [longest_common_prefix(["lower", "low", "light"]), "l"],
    [longest_common_prefix([ "SYSTEMATISE", "SYSTEMATISED", "SYSTEMATISER", "SYSTEMATISERS", "SYSTEMATISES", "SYSTEMATISING", "SYSTEMATISM", "SYSTEMATISMS", "SYSTEMATIST"]), "SYSTEMATIS"],
    [longest_common_prefix(["garden", "gardener", "gardened", "gardenful", "gardenia"]), "garden"],
    [longest_common_prefix(["flytrap", "flyway", "flyweight", "flywheel"]), "fly"],
    [longest_common_prefix(["flower", "flow", ""]), ""],
]
""",
    },
    52: {
        "markdown": """
### Cheapest flight with at most k stops
You are given `n` cities connected by a number of `flights` represented as an array where flights[i] = [from, to, cost] indicate a flight from city `from` to city `to` that costs `cost`. 

You are also given three integers `src`, `dst` and `k`. Find the cheapest cost from `src` to `dst` with at most `k` stops. 

Return -1 if there's no such route.

### Example
```
Input: n = 4, flights = [[0,1,100],[1,2,100],[2,0,100],[1,3,600],[2,3,200]], src = 0, dst = 3, k = 1
output = 700
```
""",
        "title": "Cheapest flight with at most k stops",
        "level": "Steady",
        "code": """def cheapest_flight(n: int, flights: list[list[int]], src: int, dst: int, k: int) -> int:
""",
        "test_cases": """
f1 = {  # basic
    "n": 4,
    "flights": [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]],
    "src": 0,
    "dst": 3,
    "k": 1,
    "expected": 700,  # 0→2→1→3
}
f2 = {  # cheaper path requires more stops
    "n": 4,
    "flights": [[0, 1, 100], [1, 3, 100], [0, 2, 50], [2, 1, 10], [2, 3, 200]],
    "src": 0,
    "dst": 3,
    "k": 2,
    "expected": 160,  # 0→2→1→3
}
f3 = {  # fails if heap isn't sorted by cost
    "n": 4,
    "flights": [[0, 1, 1], [1, 2, 100], [0, 2, 50], [2, 3, 1], [1, 3, 100]],
    "src": 0,
    "dst": 3,
    "k": 2,
    "expected": 51,  # 0→2→3
}
f4 = {  # same node reached with fewer stops but higher cost
    "n": 5,
    "flights": [[0, 1, 10], [1, 2, 10], [0, 2, 50], [2, 3, 10], [3, 4, 10]],
    "src": 0,
    "dst": 4,
    "k": 3,
    "expected": 40,  # 0→1→2→3→4
}
f5 = {  # cycles present
    "n": 3,
    "flights": [[0, 1, 1], [1, 0, 1], [1, 2, 1]],
    "src": 0,
    "dst": 2,
    "k": 10,
    "expected": 2,
}
f6 = {  # large k but unreachable destination
    "n": 4,
    "flights": [[0, 1, 10], [1, 2, 10]],
    "src": 0,
    "dst": 3,
    "k": 100,
    "expected": -1,
}
test_cases = [
    [
        cheapest_flight(f1["n"], f1["flights"], f1["src"], f1["dst"], f1["k"]),
        f1["expected"],
    ],
    [
        cheapest_flight(f2["n"], f2["flights"], f2["src"], f2["dst"], f2["k"]),
        f2["expected"],
    ],
    [
        cheapest_flight(f3["n"], f3["flights"], f3["src"], f3["dst"], f3["k"]),
        f3["expected"],
    ],
    [
        cheapest_flight(f4["n"], f4["flights"], f4["src"], f4["dst"], f4["k"]),
        f4["expected"],
    ],
    [
        cheapest_flight(f5["n"], f5["flights"], f5["src"], f5["dst"], f5["k"]),
        f5["expected"],
    ],
    [
        cheapest_flight(f6["n"], f6["flights"], f6["src"], f6["dst"], f6["k"]),
        f6["expected"],
    ],
]
""",
    },
    53: {
        "markdown": """
### Network delay time 
Given a network of `n` nodes, labelled 1 to n and a list of travel `times` as directed edges where times[i] = (u, v, w) with u being the source, v the target and w the time it takes for a signal to travel from u to v. 

Find the minimum time it takes for a signal from a source node `k` to reach all the other nodes. 

Return -1 if it's impossible for all the nodes to receive the signal. 

### Example
```
Input: times = [[2,1,1],[2,3,1],[3,4,1]], n = 4, k = 2
output = 2
```
""",
        "title": "Network delay time",
        "level": "Steady",
        "code": """def min_time(times: list[list[int]], n: int, k: int) -> int:
""",
        "test_cases": """
network = [[i, i + 1, i * 100] for i in range(1, 10)] + [[i, i + 2, 100] for i in range(1, 10, 2)] + [[10, 1, 10_000]]
test_cases = [
    [min_time([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2), 2],
    [min_time([[1, 2, 1]], 2, 1), 1],
    [min_time([[1, 2, 1]], 4, 2), -1],
    [min_time([[1, 2, 6]], 2, 1), 6],
    [min_time([[1, 2, 6]], 2, 2), -1],
    [min_time(network, 11, 1), 1300],
    [min_time(network, 11, 2), 11400],
    [min_time(network, 11, 11), -1],
    [min_time(network, 11, 5), 11500],
]
""",
    },
    54: {
        "markdown": """
### Critical connections
Given `n` servers labelled 0 to n - 1 connected by undirected `connections` where connections[i] = [a, b] indicates a connection between servers a and b. Return all the critical connections in the network in any order. 

> A critical connection is one that, if removed, will make some servers not be able to reach the rest of the server network. 

### Examples
```
Input: n = 4, connections = [[0,1],[1,2],[2,0],[1,3]]
output = [[1,3]]

Input: n = 2, connections = [[0,1]]
output = [[0,1]]
```
""",
        "title": "Critical connections",
        "level": "Edgy",
        "code": """def critical_connections(n: int, connections: list[list[int]]) -> list[list]:
""",
        "test_cases": """
network1 = [[0, 4], [0, 8], [0, 1], [0, 2], [0, 3], [8, 4], [4, 5], [5, 3], [3, 6], [6, 7], [1, 7]]
network2 = [[i, i + 1] for i in range(10)]
network3 = [[i, i + 1] for i in range(10)] + [[10, 1]]
test_cases = [
    [critical_connections(4, [[0, 1], [1, 2], [2, 0], [1, 3]]), [[1, 3]]],
    [critical_connections(7, [[0, 1], [1, 2], [2, 0], [1, 3], [1, 4], [4, 5], [5, 6]]), [[1, 3], [5, 6], [4, 5], [1, 4]]],
    [critical_connections(7, [[0, 1], [1, 2], [2, 0], [1, 3], [1, 4], [4, 5], [5, 6], [2, 6]]), [[1, 3]]],
    [critical_connections(9, network1), [[0, 2]]],
    [critical_connections(11, network2), [[i, i +1] for i in range(9, -1, -1)]],
    [critical_connections(11, network3), [[0, 1]]],
]
""",
    },
    55: {
        "markdown": """
### Job scheduling
Given arrays `start_time`, `end_time` and `profit` representing `n` jobs with the ith job scheduled to be done from start_time[i] to end_time[i] generating profit[i]. Find the maximum profit you can make from the jobs

If you choose a job that ends at time x you can be able to choose another one that starts at time x. 

### Example
```
Input: start_time = [1,2,3,3], end_time = [3,4,5,6], profit = [50,10,40,70]
output = 120

Input: start_time = [1,1,1], end_time = [2,3,4], profit = [5,6,4]
output = 6
```
""",
        "title": "Job scheduling",
        "level": "Steady",
        "code": """def job_schedule(start_time: list[int], end_time: list[int], profit: list[int]) -> int:
""",
        "test_cases": """
test_cases = [
    [job_schedule([1, 2, 3, 3], [3, 4, 5, 6], [50, 10, 40, 70]), 120],
    [job_schedule([1, 2, 3, 4, 6], [3, 5, 10, 6, 9], [20, 20, 100, 70, 60]), 150],
    [job_schedule([1, 1, 1], [2, 3, 4], [5, 6, 4]), 6],
    [job_schedule([i for i in range(1, 1000)], [i + 5 for i in range(1000)], [10] * 10), 30],
    [job_schedule([1] * 1000, [2] * 1000, [60] * 1000), 60],
    [job_schedule([1] * 1000, [2] * 1000, [60 * i for i in range(1000)]), 59940],
]
""",
    },
    56: {
        "markdown": """
### Fewest coins to make change
Given an integer array `coins` representing coins of different denominations and an integer `amount` representing the total amount of money, return the minimum number of coints that you need to make up that amount. 

Return -1 if `amount` cannot be made by any combination of the coins. 

You may assume that you have an infinite number of each kind of coin.

### Example
```
Input: coins = [1,2,5], amount = 11
output = 3
How: 11 = 5 + 5 + 1
```
""",
        "title": "Coin change I",
        "level": "Steady",
        "code": """def min_coins(coins: list[int], amount: int) -> int:
""",
        "test_cases": """
test_cases = [
    [min_coins([1, 2, 5], 11), 3],
    [min_coins([1, 2, 5, 10], 11), 2],
    [min_coins([1], 0), 0],
    [min_coins([1, 2, 5, 10, 20], 11), 2],
    [min_coins([1, 2, 5, 10, 20], 110), 6],
    [min_coins([2, 5], 3), -1],
    [min_coins([1, 2, 5, 10, 20], 63), 5],
    [min_coins([1, 2, 5, 10, 20, 50], 16), 3],
    [min_coins([1, 2, 5, 10, 20, 50], 28), 4],
    [min_coins([1, 2, 5, 10, 20, 50], 77), 4],
]
""",
    },
    57: {
        "markdown": """
### Min cost tickets
Given an array `days` representing planned annual train travalling days and `costs` where costs = [daily, weekly, monthly] indicating the daily (1 day), weekly (7 days) and monthly (30 days) ticket costs respectively, return the minimum cost for travelling every day in the given list of days. 

Each day is an integer between 1 and 365.

### Example
```
Input: days = [1,4,6,7,8,20], costs = [2,7,15]
output = 11
```
""",
        "title": "Min cost tickets",
        "level": "Steady",
        "code": """def min_cost_tickets(days: list[int], costs: list[int]) -> int:
""",
        "test_cases": """
test_cases = [
    [min_cost_tickets([1, 4, 6, 7, 8, 20], [2, 7, 15]), 11],
    [min_cost_tickets([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 30, 31], [2, 7, 15]), 17],
    [min_cost_tickets([1, 2, 3, 4, 5, 6, 7], [2, 7, 15]), 7],
    [min_cost_tickets([i for i in range(1, 31)], [2, 7, 15]), 15],
    [min_cost_tickets([1, 4, 6], [2, 7, 15]), 6],
    [min_cost_tickets([5, 6, 7, 8, 9, 10, 11], [2, 7, 15]), 7],
    [min_cost_tickets([5, 6, 7, 8, 9, 10, 11, 210, 211, 212, 213, 365], [2, 7, 15]), 16],
    [min_cost_tickets([i for i in range(1, 366)], [2, 7, 15]), 190],
]
""",
    },
    58: {
        "markdown": """
### Max loot binary tree
Given the `root` of a binary tree where each node represents the amount of cash stashed in a boat, return the maximum amount that you can steal from the boats given that you cannot steal from any directly connected boats i.e parent node and child node. 

### Example
```
Input: root = [9, 8, 16]
output = 24
How: Maximum amount of cash is 8 + 16 = 24 
```
""",
        "test_cases": f"""
{binary_tree}
root1 = array_to_tree([3,2,3,None,3,None,1])
root2 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1] * 100_000)
root3 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, None, None, 1])
# bst
root4 = array_to_tree([9, 8, 16])
root5 = array_to_tree([9, 8, 16, 4])
root6 = array_to_tree([])
root7 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
root8 = sorted_to_bst([i for i in range(100)])

test_cases = [
    [max_loot_tree(root1), 7],
    [max_loot_tree(root2), 286381],
    [max_loot_tree(root3), 33],
    [max_loot_tree(root4), 24],
    [max_loot_tree(root5), 24],
    [max_loot_tree(root6), 0],
    [max_loot_tree(root7), 1700],
    [max_loot_tree(root8), 2824],
]
""",
        "title": "Max loot binary tree",
        "level": "Steady",
        "code": """def max_loot_tree(root):
""",
    },
    59: {
        "markdown": """
### Lowest common ancestor 
Given the `root` of a binary tree and two nodes `p` and `q`, find the lowest common ancestor (LCA) of p and q.

> According to the definition of LCA on Wikipedia: “The lowest common ancestor is defined between two nodes p and q as the lowest node in a tree that has both p and q as descendants (where a node can be a descendant of itself).”

### Example
```
Input: root = [9, 8, 16], p = 8, q = 16
output = 9
```
""",
        "test_cases": f"""
{binary_tree}
root1 = array_to_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
root2 = array_to_tree([1, 2])
root3 = sorted_to_bst([i for i in range(100)])
test_cases = [
    [lca(root1, 6, 8), 3],
    [lca(root2, 2, 1), 1],
    [lca(root3, 0, 4), 4],
    [lca(root3, 7, 17), 12],
    [lca(root3, 39, 89), 50],
    [lca(root3, 67, 98), 75],
]
""",
        "title": "Lowest common ancestor",
        "level": "Steady",
        "code": """def lca(root, p, q):
""",
    },
    60: {
        "markdown": """
### Same binary tree 
Check if two binary trees `p` and `q` are the same given their roots. 

> Two binary trees are considered the same if they are structurally identical, and the nodes have the same value.

### Example
```
Input: p = [1,2,3], q = [1,2,3]
output = true

Input: p = [1,2], q = [1,null,2]
output = false
```
""",
        "test_cases": f"""
{binary_tree}
root1 = array_to_tree([6, 3, 9, None, 5, 4, 9])
root2 = array_to_tree([6, 3, 9, None, 5, 4, 9])
root3 = sorted_to_bst([i for i in range(100)])
root4 = sorted_to_bst([i for i in range(100)])
root5 = array_to_tree([])
root6 = array_to_tree([])
root7 = array_to_tree([1, 2])
root8 = array_to_tree([1, None, 2])
root9 = array_to_tree([1, 2, 3, 4, 5, None, 6])
root10 = array_to_tree([[1, 2, 3, 4, 5, 7, 6]])
test_cases = [
    [same_tree(root1, root2), True],
    [same_tree(root3, root4), True],
    [same_tree(root2, root3), False],
    [same_tree(root5, root6), True],
    [same_tree(root4, root6), False],
    [same_tree(root7, root8), False],
    [same_tree(root8, root8), True],
    [same_tree(root9, root10), False],
]
""",
        "title": "Same binary tree",
        "level": "Breezy",
        "code": """def same_tree(p, q):
""",
    },
    61: {
        "markdown": """
### Binary tree cousins
Given the `root` of a binary tree with unique values and the value of two different nodes in the tree `x` and `y`, check whether x and y are cousins. 

> Two nodes of a binary tree are cousins if they have the same depth with different parents.

### Example
```python
# Input: root = [100, 50, 600, 45, 55, 500, 1000]), x = 45, y = 500
# output = True
# Why: both are at the same level and 45's parent is 50 while 500's parent is 600
```
""",
        "test_cases": f"""
{binary_tree}
root1 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, None, None, 1])
root2 = array_to_tree([9, 8, 16])
root3 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
root4 = sorted_to_bst([i for i in range(100)])
test_cases = [
    [are_cousins(root1, 11, 13), True],
    [are_cousins(root1, 7, 4), False],
    [are_cousins(root2, 9, 16), False],
    [are_cousins(root3, 55, 500), True],
    [are_cousins(root4, 4, 13), True],
    [are_cousins(root4, 51, 92), True],
]
""",
        "title": "Binary tree cousins",
        "level": "Steady",
        "code": """def are_cousins(root, x, y):
""",
    },
    62: {
        "markdown": """
### How many islands
Given an `m x n grid` where each value is either 1 or 0 with 1 indicating land and 0 indicating water, return the number of islands in the grid. You may assume all four edges of the grid are surrounded by water. 

> An island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically.

### Examples
Input: grid = [[1, 1, 1, 1], [0, 0, 0, 0], [1, 1, 1, 1]]
output = 2  # 2 horizontal islands. 
""",
        "test_cases": f"""
g1 = [['1', '1', '1', '1'], ['0', '0', '0', '0'], ['1', '1', '1', '1']]
g2 = [['1', '0', '1', '1'], ['0', '0', '1', '0'], ['1', '1', '1', '1']]
g3 = [[]]
g4 = [['1', '0', '1', '0', '1'] for _ in range(10_000)]
g5 = [['0', '1', '0', '0', '1'] for _ in range(10_000)]
g6 = [['1', '0', '1', '0', '1'] * 10_000]
g7 = [[('1' if (i + j) % 2 else '0') for i in range(6_000)] for j in range(4)]
g8 = [['1']]
g9 = [['0']]
test_cases = [
    [count_islands(g1), 2],
    [count_islands(g2), 2],
    [count_islands(g3), 0],
    [count_islands(g4), 3],
    [count_islands(g5), 2],
    [count_islands(g6), 20001],
    [count_islands(g7), 12000],
    [count_islands(g8), 1],
    [count_islands(g9), 0],
]
""",
        "title": "How many islands",
        "level": "Steady",
        "code": """def count_islands(grid: list[list[int]]) -> int:
""",
    },
    63: {
        "markdown": """
### Merge intervals
Given an array of `intervals` merge all overlapping intervals. 

### Example
```
input: [[1, 5], [5, 10]]
output = [[1, 10]]
```
""",
        "title": "Merge intervals",
        "level": "Steady",
        "code": """def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
""",
        "test_cases": """
intervals1 = [[1, 10], [2, 3], [4, 8], [9, 12], [11, 15], [16, 18], [17, 20]]
intervals2 = [[5, 7], [1, 3], [2, 6], [8, 10], [9, 12], [15, 18], [17, 20], [19, 22]]
intervals3 = [[1, 2], [2, 3], [3, 4], [5, 6], [6, 8], [8, 10], [10, 12]]
intervals4 = [[0, 5], [1, 4], [2, 3] ,[10, 15], [12, 18], [14, 16], [30, 35], [32, 40], [41, 45]]
intervals5 = [[1, 4], [3, 5], [6, 8], [7, 9], [10, 14], [12, 15], [16, 18], [17, 19], [20, 25], [22, 30], [28, 35], [36, 40]]
intervals6 = [[i, i + 1] for i in range(100_000)]
test_cases = [
    [merge_intervals([[1,3],[2,6],[8,10],[15,18]]), [[1,6],[8,10],[15,18]]],
    [merge_intervals([[1, 5], [5, 10]]), [[1, 10]]],
    [merge_intervals([[3, 11], [2, 6]]), [[2, 11]]],
    [merge_intervals(intervals1), [[1, 15], [16, 20]]],
    [merge_intervals(intervals2), [[1, 7], [8, 12], [15, 22]]],
    [merge_intervals(intervals3), [[1, 4], [5, 12]]],
    [merge_intervals(intervals4), [[0, 5], [10, 18], [30, 40], [41, 45]]],
    [merge_intervals(intervals5), [[1, 5], [6, 9], [10, 15], [16, 19], [20, 35], [36, 40]]],
    [merge_intervals(intervals6), [[0, 100_000]]],
]
""",
    },
    64: {
        "markdown": """
### longest increasing subsequence
Given an array `nums` of integers return the length of the longest strictly increasing subsequence

### Example
```
input: [10,9,2,5,3,7,101,18]
output = 4
How: LIS is [2, 3, 7, 101] with length 4. 
```
""",
        "title": "Longest increasing subsequence",
        "level": "Steady",
        "code": """def lis(nums: list[int]) -> int:
""",
        "test_cases": """
nums1 = [i for i in range(10_000)]
nums2 = [1 for _ in range(10_000)]
nums3 = [10, 9, 2, 5, 3, 7, 101, 18]
nums4 = [0, 1, 0, 3, 2, 3]
test_cases = [
    [lis([0,1,0,3,2,3]), 4],
    [lis([6,6,6,6,6,6,6,6]), 1],
    [lis([10,9,2,5,3,7,101,18]), 4],
    [lis(nums1), 10_000],
    [lis(nums2), 1],
    [lis(nums3), 4],
    [lis(nums4), 4],
]
""",
    },
    65: {
        "markdown": """
### Longest palidromic substring
Given a string `s`, return the longest palindromic substring in s. 

Return the first one if there are multiple longest palindromic substrings. 

### Example
```
s = "babad"
output = "bab" 

s = "abcde"
output = "a"
```
""",
        "title": "Longest palindromic substring",
        "level": "Steady",
        "code": """def lps(s: str) -> str:
""",
        "test_cases": """
test_cases = [
    [lps("babad"), "bab"],
    [lps("abcde"), "a"],
    [lps("ab" * 100), 'a' + "ba" * 99],
    [lps("a" * 100), "a" * 100],
    [lps("abcdefghijklmnopqrstuvwxyz"), "a"],
    [lps('a' * 1000 + 'b' + 'a' * 1000), 'a' * 1000 + 'b' + 'a' * 1000],
    [lps('a' * 1000 + 'b' + 'a' * 50), 'a' * 1000 ],
]
""",
    },
    66: {
        "markdown": """
### Permutations
Given a string `s` all lowercase characters and a positive integer `k`, return all the possible permutations of string `s` of size k.  

Return the permutations in any order. 

Can you do it without python's itertools?

### Example
```
s = 'art'
k = 2
output = ['ar', 'at', 'ra', 'rt', 'ta', 'tr']
```
""",
        "test_cases": """
def PERMUTATIONS(s, k=None):
    results, n = [], len(s)
    k = n if not k else k

    def backtrack(path, used):
        if len(path) == k:
            return results.append(path)
        for i in range(n):
            if used[i]:
                continue
            path += s[i]
            used[i] = True
            backtrack(path, used)
            path = path[:-1]
            used[i] = False

    backtrack('', [False for _ in range(n)])
    return results

s1, k1 = 'art', 2
s2, k2 = '', 3
s3, k3 = 'rat', 3 
s4, k4 = 'rat', 1 
s5, k5 = 'rat', 0
s6, k6 = 'abcdefghijklmnopqrstuvwxyz', 1
s7, k7 = 'abcdefghijk', 5
s8, k8 = 'xyz', 4
from collections import Counter 
test_cases = [
    [Counter(perms(s1, k1)), Counter(PERMUTATIONS(s1, k1))],
    [Counter(perms(s2, k2)), Counter(PERMUTATIONS(s2, k2))],
    [Counter(perms(s3, k3)), Counter(PERMUTATIONS(s3, k3))],
    [Counter(perms(s4, k4)), Counter(PERMUTATIONS(s4, k4))],
    [Counter(perms(s5, k5)), Counter(PERMUTATIONS(s5, k5))],
    [Counter(perms(s6, k6)), Counter(PERMUTATIONS(s6, k6))],
    [Counter(perms(s7, k7)), Counter(PERMUTATIONS(s7, k7))],
    [Counter(perms(s8, k8)), Counter(PERMUTATIONS(s8, k8))],
]
""",
        "title": "Permutations",
        "level": "Steady",
        "code": """def perms(nums: str, k: int) -> list[str]:
""",
    },
    67: {
        "markdown": """
### Combinations
Given a string `s` and a positive integer `k`, return all possible combinations of s of size k.

Return the combinations in any order.

Are your hands tied without python's itertools 😅?

### Example
```
input: s = "abcd", k = 3
output = ['abc', 'abd', 'acd', 'bcd']
```
""",
        "test_cases": """
def COMBINATIONS(s, k):
    results = []

    def backtrack(start, temp):
        if len(temp) == k:
            return results.append(temp)
        for i in range(start, len(s)):
            temp += s[i]
            backtrack(i + 1, temp)
            temp = temp[:-1]

    backtrack(0, "")
    return results

s1, k1 = 'abcd', 3
s2, k2 = '', 2 
s3, k3 = 'rat', 3 
s4, k4 = 'rat', 1 
s5, k5 = 'rat', 0
s6, k6 = 'abcdefghijklmnopqrstuvwxyz', 1
s7, k7 = 'abcdefghijklmnopqrstuvwxyz', 5
s8, k8 = 'abcd', 5
from collections import Counter 
test_cases = [
    [Counter(combs(s1, k1)), Counter(COMBINATIONS(s1, k1))],
    [Counter(combs(s2, k2)), Counter(COMBINATIONS(s2, k2))],
    [Counter(combs(s3, k3)), Counter(COMBINATIONS(s3, k3))],
    [Counter(combs(s4, k4)), Counter(COMBINATIONS(s4, k4))],
    [Counter(combs(s5, k5)), Counter(COMBINATIONS(s5, k5))],
    [Counter(combs(s6, k6)), Counter(COMBINATIONS(s6, k6))],
    [Counter(combs(s7, k7)), Counter(COMBINATIONS(s7, k7))],
    [Counter(combs(s8, k8)), Counter(COMBINATIONS(s8, k8))],
]
""",
        "title": "Combinations",
        "level": "Steady",
        "code": """def combs(s: str, k: int) -> list[str]:
""",
    },
    68: {
        "markdown": """
### Calendar add event
Design `MyCalendar` with a method `book(start: int, end: int) -> bool` that can add an event to the calendar. The book method should return true if an event can be successfully added or false otherwise.

### Example
```python
calendar = MyCalendar()
calendar.book(10, 20)  # True
calendar.book(10, 20)  # False - already booked
calendar.book(15, 25)  # False - overlapping with [10, 20)
calendar.book(20, 30)  # True  - new event can start at the end time of another
```
""",
        "test_cases": f"""
calendar = MyCalendar()
test_cases = [
    [calendar.book(10, 20), True],
    [calendar.book(10, 20), False],
    [calendar.book(15, 25), False],
    [calendar.book(20, 30), True],
    [calendar.book(30, 31), True],
    [calendar.book(100, 2000), True],
    [calendar.book(2_000, 6_000_000), True],
    [calendar.book(3_000, 50_000), False],
    [calendar.book(10_000, 20_000), False],
    [calendar.book(0, 6_000_000), False],
    [calendar.book(55_556, 3_000_000), False],
    [calendar.book(2000, 2020), False],
    [calendar.book(5_999_999, 6_000_001), False],
    [calendar.book(100_000, 200_000), False],
    [calendar.book(31, 41), True],
    [calendar.book(42, 50), True],
    [calendar.book(50, 60), True],
    [calendar.book(60, 70), True],
    [calendar.book(70, 80), True],
    [calendar.book(80, 90), True],
    [calendar.book(90, 100), True],
]
""",
        "title": "Calendar book event",
        "level": "Steady",
        "code": """class MyCalendar:
""",
    },
    69: {
        "markdown": """
### Range frequency query 
Given an `arr` design a data structure `RangeFreq` with a method `query(left: int, right: int, value: int) -> int` that returns the number of times the given value occurs in the subarray arr[left...right] (both left and right inclusive)

### Example
```
arr = [1, 3, 7, 7, 7, 3, 4, 1, 7]
rf = RangeFreq(arr)

input: rf.query(2, 5, 7)
output = 3  # 7 appears 3 times between indices 1 and 6

input: rf.query(2, 4, 7)  
output = 3 

input: rf.query(0, 8, 1)
output = 2 

input: rf.query(4, 7, 4)
output = 1
```
""",
        "test_cases": f"""
arr = [1, 3, 7, 7, 7, 3, 4, 1, 7]
rf1 = RangeFreq(arr)
arr2 = [i for i in range(100_000)]
rf2 = RangeFreq(arr2)
arr3 = [i for i in range(1, 100_000)] + [22] * 50_000 + [-15] * 100_000
rf3 = RangeFreq(arr3)
test_cases = [
    [rf1.query(2, 4, 7), 3],
    [rf1.query(0, 8, 1), 2],
    [rf1.query(4, 7, 4), 1],
    [rf1.query(2, 4, 9), 0],
    [rf1.query(8, 8, 7), 1],
    [rf2.query(0, 100_000, 897), 1],
    [rf2.query(0, 100_000, 0), 1],
    [rf2.query(0, 100_000, 99_999), 1],
    [rf2.query(0, 10, 7), 1],
    [rf2.query(50_000, 50_000, 50_000), 1],
    [rf3.query(0, 250_000, 0), 1],
    [rf3.query(0, 250_000, 22), 50_001],
    [rf3.query(0, 250_000, -5), 100_000],
    [rf3.query(100_000, 150_000, 22), 50_000],
    [rf3.query(100_000, 150_005, -15), 5],
]
""",
        "title": "Range frequency query",
        "level": "Steady",
        "code": """class RangeFreq:
""",
    },
    70: {
        "markdown": """
### Invert binary tree
Given the `root` of a binary tree, invert the tree, and return its root.

### Examples
Input: root = [2,1,3]
output = [2,3,1]

Input: root = []
output = []
""",
        "test_cases": f"""
{binary_tree}
def INVERT_TREE(root):
    if not root:
        return None
    root.left, root.right = root.right, root.left
    INVERT_TREE(root.left)
    INVERT_TREE(root.right)
    return root

root1 = array_to_tree([4, 2, 7, 1, 3, 6, 9])
root2 = array_to_tree([4, 7, 2, 9, 6, 3, 1])
root3 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, None, None, 1])
root4 = array_to_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1] * 100_000)
root5 = array_to_tree([9, 8, 16])
root6 = array_to_tree([12, 3, 20, None, 5])
root7 = array_to_tree([])
root8 = array_to_tree([100, 50, 600, 45, 55, 500, 1000])
root9 = sorted_to_bst([i for i in range(100)])

test_cases = [
    [same_tree(invert_tree(root1), INVERT_TREE(root1)), True],
    [same_tree(invert_tree(root2), INVERT_TREE(root2)), True],
    [same_tree(invert_tree(root3), INVERT_TREE(root3)), True],
    [same_tree(invert_tree(root4), INVERT_TREE(root4)), True],
    [same_tree(invert_tree(root5), INVERT_TREE(root5)), True],
    [same_tree(invert_tree(root6), INVERT_TREE(root6)), True],
    [same_tree(invert_tree(root7), INVERT_TREE(root7)), True],
    [same_tree(invert_tree(root8), INVERT_TREE(root8)), True],
    [same_tree(invert_tree(root9), INVERT_TREE(root9)), True],
]
""",
        "title": "Invert binary tree",
        "level": "Steady",
        "code": """def invert_tree(root):
""",
    },
    71: {
        "markdown": """
### Min Stack

Design a stack `Stack` that supports:

- `push` - add value to stack
- `pop` - removes element on top of the stack
- `top` - returns the top element of the stack
- `get_min` - returns the minimum element in the stack

  All in **O(1)** time.

### Example
```
stack = Stack()
stack.push(1)   # adds 1 to the stack 
stack.push(2)   # adds 2 to the stack
stack.push(3)   # adds 3 to the stack
stack.top()     # returns 3
stack.pop()     # removes 3 from stack 
stack.get_min() # returns 1 
```
""",
        "test_cases": f"""
stack1 = Stack()
for i in range(1, 5):
    stack1.push(i)
stack2 = Stack()
for i in range(100_000, 10, -2):
    stack2.push(i)
test_cases = [
    [stack1.top(), 4],
    [stack1.get_min(), 1],
    [stack1.top(), 4],
    [stack1.pop(), None],
    [stack1.top(), 3],
    [stack2.top(), 12],
    [stack2.pop(), None],
    [stack2.get_min(), 14],
    [stack2.push(3), None],
    [stack2.get_min(), 3],
]
""",
        "title": "Min stack",
        "level": "Steady",
        "code": """class Stack:
""",
    },
    72: {
        "markdown": """
### LRU Cache
Design a data structure that follows the constraints of a Least Recently Used (LRU) cache:
- `LRUCache(capacity: int)` - initialize LRU cache with capacity
- `put(key: int, value: int)` - add key value pair to cache or update value if key exists. If number of keys exceeds capacity, evict the least recently used key. 
- `get(key: int)` - return value of key if key exists, else return -1

`get` and `put` must run in constant time **O(1)**

### Example
```python
cache = LRUCache(3)
cache.put(1, 10) # {1:10}
cache.put(2, 20) # {1:10, 2:20}
cache.put(3, 30) # {1:10, 2:20, 3:30}
cache.get(3)     # return 30
cache.get(4)     # return -1 
cache.get(2)     # return 20
cache.put(4, 40) # {2:20, 3:30, 4:40}  # evict LRU key 1:10
cache.get(1)     # return -1
```
""",
        "test_cases": f"""
cache = LRUCache(100_000)
for i in range(1, 150_000):
    cache.put(i, i * 10) # 49,999 - 149,999
test_cases = [
    [cache.get(100_000), 1_000_000],
    [cache.get(49_999), -1],
    [cache.get(49_998), -1],
    [cache.get(10), -1],
    [cache.get(149_999), 1_499_990],
    [cache.put(2, 20), None],
    [cache.get(49_999), -1],
]
""",
        "title": "LRU Cache",
        "level": "Steady",
        "code": """class LRUCache:
""",
    },
    73: {
        "markdown": """
### Reverse a linked list
Given the `head` of a linked list, reverse the list, and return its head

### Example
```
input: [1, 2, 3, 4, 5, 6]
output = [6, 5, 4, 3, 2, 1]
```
""",
        "test_cases": f"""
{linked_list}
def REVERSE_LIST(head):
    prev = None
    curr = head

    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt

    return prev

l1 = array_to_list([1, 2, 3, 4, 5, 6])
l1_ = array_to_list([1, 2, 3, 4, 5, 6])
l2 = array_to_list([i for i in range(100_000)])
l2_ = array_to_list([i for i in range(100_000)])
l3 = array_to_list([3] * 100_000)
l3_ = array_to_list([3] * 100_000)
l4 = array_to_list([])
l4_ = array_to_list([])
l5 = array_to_list([6] + [0] * 99_999 + [9])
l5_ = array_to_list([6] + [0] * 99_999 + [9])
l6 = array_to_list([i for i in range(-100_000, 0)])
l6_ = array_to_list([i for i in range(-100_000, 0)])
test_cases = [
    [same_list(reverse_list(l1), REVERSE_LIST(l1_)), True],
    [same_list(reverse_list(l2), REVERSE_LIST(l2_)), True],
    [same_list(reverse_list(l3), REVERSE_LIST(l3_)), True],
    [same_list(reverse_list(l4), REVERSE_LIST(l4_)), True],
    [same_list(reverse_list(l5), REVERSE_LIST(l5_)), True],
    [same_list(reverse_list(l6), REVERSE_LIST(l6_)), True],
]
""",
        "title": "Reverse linked list",
        "level": "Steady",
        "code": """def reverse_list(head)
""",
    },
    74: {
        "markdown": """
### Merge two sorted linked lists
Given two sorted linked lists, `head1` and `head2`. Merge them into one sorted linked list and return the head of the merged list. 

### Example
```
input: head1 = [2, 4, 6, 6, 12, 22], head2 = [3, 7, 8, 9]
output = [2, 3, 4, 6, 6, 7, 8, 9, 12, 22]
```
""",
        "test_cases": f"""
{linked_list}
l1 = array_to_list([2, 4, 6, 6, 12, 22])
l2 = array_to_list([3, 7, 8, 9])
l12 = array_to_list([2, 3, 4, 6, 6, 7, 8, 9, 12, 22])
l3 = array_to_list([])
l4 = array_to_list([0])
l5 = array_to_list([2])
l6 = array_to_list([2])
l56 = array_to_list([2, 2])
l7 = array_to_list([i for i in range(60_000)])
l8 = array_to_list([i for i in range(-100, 0)])
l78 = array_to_list([i for i in range(-100, 60_000)])
l9 = array_to_list([1] * 1000)
l10 = array_to_list([2] * 2000)
l910 = array_to_list([1] * 1000 + [2] * 2000)
test_cases = [
    [same_list(list_merge(l1, l2), l12), True],
    [same_list(list_merge(l3, l3), l3), True],
    [same_list(list_merge(l3, l4), l4), True],
    [same_list(list_merge(l5, l6), l56), True],
    [same_list(list_merge(l7, l8), l78), True],
    [same_list(list_merge(l9, l10), l910), True],
]
""",
        "title": "Merge sorted linked lists",
        "level": "Steady",
        "code": """def list_merge(head1, head2):
""",
    },
    75: {
        "markdown": """
### Sum linked lists
You are given two non-empty linked lists, `head2` and `head2` representing two non-negative integers. The digits are stored in reverse order, and each of their nodes contains a single digit.

Add the two numbers and return the sum as a linked list. You may assume the two numbers do not contain any leading zero, except the number 0 itself.

### Example
```
input: head1 = [2, 4, 3], head2 = [5, 6, 4]
output = [7, 0, 8]
explanation: 342 + 465 = 807
```
""",
        "test_cases": f"""
{linked_list}
l1 = array_to_list([2, 4, 3])
l2 = array_to_list([5, 6, 4])
l3 = array_to_list([9, 9, 9, 9, 9, 9, 9])
l4 = array_to_list([9, 9, 9, 9])
l5 = array_to_list([])
l6 = array_to_list([2])
l7 = array_to_list([1] * 60_001)
l12 = array_to_list([7, 0, 8])
l34 = array_to_list([8, 9, 9, 9, 0, 0, 0, 1])
l67 = array_to_list([3] + [1] * 60_000)
test_cases = [
    [same_list(list_add(l1, l2), l12), True],
    [same_list(list_add(l3, l4), l34), True],
    [same_list(list_add(l5, l6), l6), True],
    [same_list(list_add(l5, l5), l5), True],
    [same_list(list_add(l7, l5), l7), True],
    [same_list(list_add(l7, l6), l67), True],
]
""",
        "title": "Sum linked lists",
        "level": "Steady",
        "code": """def list_add(head1, head2):
""",
    },
    76: {
        "markdown": """
### Triplet sum equals zero
Given an array `nums` of integers, find all unique triplets that sum to zero. 

### Example
```
input: [-1,0,1,2,-1,-4]
output = [[-1,-1,2],[-1,0,1]]

input:  [0,1,1]
output = []

input: [0,0,0]
output = [[0,0,0]]
```
""",
        "title": "Triplets sum equals zero",
        "level": "Steady",
        "code": """def triplet_sum(nums: list[int]) -> list[list[int]]:
""",
        "test_cases": """
def TRIPLET_SUM(nums: list[int]) -> list[list[int]]:
    # time O(n ^ 2)
    nums.sort()
    res, n = [], len(nums)
    for i in range(n):
        if nums[i] > 0:
            break
        # skip duplicate anchors
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        # two pointer search
        l, r = i + 1, n -1 
        while l < r:
            total = nums[i] + nums[l] + nums[r]
            if total < 0:
                l += 1
            elif total > 0:
                r -= 1
            else:
                res.append([nums[i], nums[l], nums[r]])
                # skip duplicates for left and right 
                l += 1 
                while l < r and nums[l] == nums[l - 1]:
                    l += 1 
                r -= 1 
                while l < r and nums[r] == nums[r + 1]:
                    r -= 1 
    return res 

nums1 = [1] * 5000 + [0] * 5000 + [-1] * 5000
nums2 = [0] * 1000
nums3 = [1] * 1000 + [-1] * 1000
nums4 = [0, 1, 1]
nums5 = [0, 0, 0]
nums6 = [i for i in range(-1000, 1000)]
test_cases = [
    [triplet_sum([-1,0,1,2,-1,-4]), TRIPLET_SUM([-1,0,1,2,-1,-4])],
    [triplet_sum(nums1), TRIPLET_SUM(nums1)],
    [triplet_sum(nums2), TRIPLET_SUM(nums2)],
    [triplet_sum(nums3), TRIPLET_SUM(nums3)],
    [triplet_sum(nums4), TRIPLET_SUM(nums4)],
    [triplet_sum(nums5), TRIPLET_SUM(nums5)],
    [triplet_sum(nums6), TRIPLET_SUM(nums6)],
]
""",
    },
    77: {
        "markdown": """
### Max water held
Given an array `nums` where each number represents the height of a vertical wall, find two walls that hold the most water between them and return the units of water contained. 

> To calculate Units of water held, multiply the `width(base)` by `height`

### Example
```
input: [3, 1, 2, 7]
output = 9
how: 9 units of water held between the first and last wall

input: [1, 1]
output = 1
```
""",
        "title": "Max water held",
        "level": "Steady",
        "code": """def max_water(nums: list[int]) -> int:
""",
        "test_cases": """
h1 = [3, 1, 2, 7]
h2 = [i for i in range(100_000)]
h3 = [0] * 100_000 + h1 
h4 = [0] * 60_000 + [1]
h5 = [1] * 100_000
h6 = [100]
h7 = [1] + [0] * 50 + h1 
test_cases = [
    [max_water(h1), 9],
    [max_water(h2), 2499950000],
    [max_water(h3), 9],
    [max_water(h4), 0],
    [max_water(h5), 99_999],
    [max_water(h6), 0],
    [max_water(h7), 54],
]
""",
    },
    78: {
        "markdown": """
### Trapping rain water
Given `n` positive integers `nums` representing elevation heights where the width of each bar is 1, return how much water can be trapped after rain. 

### Example
```
input: [3, 1, 2, 7]
output = 3
how: 2 units at index 1 and 1 unit at index 2 
```
""",
        "title": "Trapping rain water",
        "level": "Edgy",
        "code": """def trap_water(nums: list[int]) -> int:
""",
        "test_cases": """
h1 = [3, 1, 2, 7]
h2 = [i for i in range(100_000)]
h3 = [0] * 100_000 + h1 
h4 = [0] * 60_000 + [1]
h5 = [100] + [0] * 100_000 + [1]
h6 = [100]
h7 = [1] + [0] * 50 + h1 
h8 = []
test_cases = [
    [trap_water(h1), 3],
    [trap_water(h2), 0],
    [trap_water(h3), 3],
    [trap_water(h4), 0],
    [trap_water(h5), 100000],
    [trap_water(h6), 0],
    [trap_water(h7), 53],
    [trap_water(h8), 0],
]
""",
    },
    79: {
        "markdown": """
### Connected cities
Given an `n * n` adjacency matrix of connected cities with each cell having values 1 or 0 where 0 indicate city i is not connected to city j and 1 indicate otherwise. 

Return the number of connected groups of cities.  

### Example
```
input: [[1,0,0],[0,1,0],[0,0,1]]
output = 3
```
""",
        "title": "Connected cities",
        "level": "Steady",
        "code": """def connected_cities(adj_mat: list[list[int]]) -> int:
""",
        "test_cases": """
m1 = [[1]]
m2 = [
    [1, 1],
    [1, 1],
]
m3 = [[1,0,0],[0,1,0],[0,0,1]]
m4 = [
    [1, 1, 1, 1],
    [1, 1, 1, 1],
    [1, 1, 1, 1],
    [1, 1, 1, 1],
]
m5 = [
    [1, 1, 0, 0],
    [1, 1, 1, 0],
    [0, 1, 1, 1],
    [0, 0, 1, 1],
]
m6 = [
    [1, 1, 0, 0, 0],
    [1, 1, 0, 0, 0],
    [0, 0, 1, 1, 0],
    [0, 0, 1, 1, 0],
    [0, 0, 0, 0, 1],
]
m7 = [
    [1, 1, 0],
    [0, 1, 1],
    [0, 0, 1],
]
m8 = [
    [0, 1, 0],
    [1, 0, 0],
    [0, 0, 0],
]
n = 100
m9 = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
n = 200
m10 = [[1] * n for _ in range(n)]
test_cases = [
    [connected_cities(m1), 1],
    [connected_cities(m2), 1],
    [connected_cities(m3), 3],
    [connected_cities(m4), 1],
    [connected_cities(m5), 1],
    [connected_cities(m6), 3],
    [connected_cities(m7), 1],
    [connected_cities(m8), 2],
    [connected_cities(m9), 100],
    [connected_cities(m10), 1],
]
""",
    },
    80: {
        "markdown": """
### Reachable cities
Given `n` cities labelled 0 to n - 1 and an array `edges` where edges[i] = [from, to, weight] represents a weighted bidirectional edge between cities `from` and `to`.  Return city with the smallest number of cities that are reachable and whose distance is at most `k`. 

If multiple such cities, return the one with the greatest number. 

### Examples
```
n = 5 
edges = [
    [0, 1, 1],
    [1, 2, 1],
    [2, 3, 1],
    [3, 4, 1],
]
k = 1
output = 4
Why: reachable counts: 0 -> 1, 1 -> 2, 2 -> 2, 4 -> 1 
```
""",
        "title": "Reachable cities",
        "level": "Steady",
        "code": """def reachable_cities(n: int, edges: list[list[int]], k: int) -> int:
""",
        "test_cases": """
n1 = 1
e1 = []
k1 = 0
# expected: 0
n2 = 2
e2 = [[0, 1, 3]]
k2 = 5
# expected: 1  (tie: both have 1 neighbor -> pick larger index)
n3 = 2
e3 = [[0, 1, 10]]
k3 = 5
# expected: 1  (both have 0 neighbors -> pick larger index)
n4 = 5
e4 = [
    [0, 1, 1],
    [1, 2, 1],
    [2, 3, 1],
    [3, 4, 1],
]
k4 = 1
# reachable counts:
# 0=1, 1=2, 2=2, 3=2, 4=1
# expected: 4
n5 = 5
e5 = [
    [0, 1, 1],
    [0, 2, 1],
    [0, 3, 1],
    [0, 4, 1],
]
k5 = 1
# counts: 0=4, others=1
# expected: 4
n6 = 6
e6 = [
    [0, 1, 1],
    [1, 2, 1],
    [3, 4, 1],
]
k6 = 2
# counts: 0=2,1=2,2=2,3=1,4=1,5=0
# expected: 5
n7 = 4
e7 = [
    [0, 1, 1],
    [0, 2, 1],
    [0, 3, 1],
    [1, 2, 1],
    [1, 3, 1],
    [2, 3, 1],
]
k7 = 2
# all cities see 3 neighbors
# expected: 3
n8 = 4
e8 = [
    [0, 1, 10],
    [0, 2, 1],
    [2, 1, 1],
    [1, 3, 1],
]
k8 = 2
# distances from 0 → {1,2} via 2
# counts: 0=2, 1=2, 2=2, 3=1
# expected: 3
n9 = 3
e9 = [
    [0, 1, 10],
    [0, 1, 1],
    [1, 2, 1],
]
k9 = 2
# counts: 0=2, 1=2, 2=1
# expected: 2
n10 = 5
e10 = [
    [0, 1, 5],
    [1, 2, 5],
    [2, 3, 5],
    [3, 4, 5],
]
k10 = 100
# all cities see 4 neighbors
# expected: 4
cities = [[0, 4, 10], [0, 8, 25], [0, 1, 10], [0, 2, 30], [0, 3, 20], [8, 4, 60], [4, 5, 60], [5, 3, 70], [3, 6, 10], [6, 7, 5], [1, 7, 50]]
test_cases = [
    [reachable_cities(9, cities, 5), 8],
    [reachable_cities(9, cities, 70), 5],
    [reachable_cities(9, cities, 1), 8],
    [reachable_cities(n1, e1, k1), 0],
    [reachable_cities(n2, e2, k2), 1],
    [reachable_cities(n3, e3, k3), 1],
    [reachable_cities(n4, e4, k4), 4],
    [reachable_cities(n5, e5, k5), 4],
    [reachable_cities(n6, e6, k6), 5],
    [reachable_cities(n7, e7, k7), 3],
    [reachable_cities(n8, e8, k8), 3],
    [reachable_cities(n9, e9, k9), 2],
    [reachable_cities(n10, e10, k10), 4],
]
""",
    },
}
