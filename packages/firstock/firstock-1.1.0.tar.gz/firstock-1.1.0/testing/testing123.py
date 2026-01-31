def longest_common_prefix(strs):
    prefix = ""

    for i in range(len(strs[0])):
        char = strs[0][i]

        for s in strs[i:]:
            if char != s[i]:
                return prefix
        prefix += char

strs = ["flower","flow","flight"]
final = longest_common_prefix(strs)
print(final)
# Time complexity = o(nm)


# Optimised logic

# Rule from lexicographical sorting:
# If two strings differ earlier, they will be farther apart in sorted order.
def longest_common_prefix_2(strs):
    strs.sort()

    first = strs[0]
    last = strs[-1]

    i=0

    while i <len(first) and i <len(last) and first[i] == last[i]:
        i+=1
    
    return first[:i]

strs = ["flower","flow","flight"]
final = longest_common_prefix_2(strs)
print(final)
# Time complexity = o(n log n+ m)


def s_elements_array(nums):
    s=0
    for i in range(len(nums)):
        s = s+nums[i]
        

    return s

nums = [1,2,3,4]
final = s_elements_array(nums)
print(final)

def largest_el(nums):
    largest = nums[0]
    for i in range(len(nums)):
        if nums[i] > largest:
            largest = nums[i]
    return largest

nums = [9,4,10,3]
final = largest_el(nums)
print(final)

#count even numbers in the array 


def even_numbers_array(nums):
    count = 0
    for i in range(len(nums)):
        if nums[i] % 2 == 0:
            count = count + 1
        
    return count 

nums = [2,1,4,6,5,8]
final = even_numbers_array(nums)
print(final)


# reverse array 
def re(nums):
    return nums[::-1]

nums = [1,2,3,4,5]
final = re(nums)
print(final)



def sml_ele(nums):
    small = nums[0]
    for i in range(len(nums)):
        if nums[i] < small:
            small = nums[i]
    return small

nums = [9,5,1,2,4]
final = sml_ele(nums)
print(final)

#check if a number is present in the array?


