-- database/seed.sql

-- Insert sample technical questions into the bank
INSERT INTO questions (category, subcategory, difficulty, problem_statement, metadata) VALUES
('Coding', 'Algorithms', 'Medium', 'Write a function to find the length of the longest substring without repeating characters. Input: s = "abcabcbb", Output: 3', '{"test_cases": [{"input": "abcabcbb", "expected": 3}, {"input": "bbbbb", "expected": 1}], "language_templates": {"python": "class Solution:\n    def lengthOfLongestSubstring(self, s: str) -> int:\n        pass"}}'::jsonb),
('Coding', 'Data Structures', 'Easy', 'Implement a function to reverse a singly linked list. Return the new head.', '{"test_cases": [], "language_templates": {"python": "class ListNode:\n    def __init__(self, val=0, next=None):\n        self.val = val\n        self.next = next\nclass Solution:\n    def reverseList(self, head: ListNode) -> ListNode:\n        pass"}}'::jsonb),
('System Design', 'Scalability', 'Hard', 'Design a URL shortening service like bit.ly. Describe the API, database schema, and how you would scale it to handle 10,000 requests per second.', '{"rubric": ["Scalability", "API Design", "Database Choice", "Caching Strategy"]}'::jsonb),
('MCQ', 'Databases', 'Medium', 'Which of the following transaction isolation levels prevents phantom reads in PostgreSQL?', '{"options": ["Read Uncommitted", "Read Committed", "Repeatable Read", "Serializable"], "correct_answer": "Serializable"}'::jsonb),
('Behavioral', 'Leadership', 'Medium', 'Describe a time when you had a conflict with a peer engineer or product manager. How did you resolve it and what was the outcome?', '{"rubric": ["Conflict Resolution", "Communication", "Empathy", "Professionalism"]}'::jsonb);
