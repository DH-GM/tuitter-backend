-- Seed Data for Social.vim Application
-- Insert demo users
INSERT INTO users (username, display_name, bio, followers, following, posts_count) VALUES
('yourname', 'Your Name', 'Building cool stuff with TUIs | vim enthusiast | developer', 891, 328, 142),
('alice', 'Alice Johnson', 'Full-stack developer | Open source contributor', 1234, 567, 89),
('bob', 'Bob Smith', 'Tech blogger | Code reviewer | Coffee enthusiast', 2345, 890, 234),
('charlie', 'Charlie Davis', 'CLI tools developer | Rust advocate', 456, 234, 67),
('techwriter', 'Tech Writer', 'Writing about technology and development', 3456, 1234, 456),
('cliexpert', 'CLI Expert', 'Terminal user interface expert', 2890, 1100, 389),
('vimfan', 'Vim Fan', 'Vim configuration enthusiast', 1567, 678, 234),
('opensource_dev', 'OpenSource Dev', 'Building tools for developers', 1200, 450, 156);

-- Insert user settings for all users
INSERT INTO user_settings (user_id, email_notifications, show_online_status, private_account, github_connected) 
SELECT id, TRUE, TRUE, FALSE, (username = 'yourname') FROM users;

-- Insert demo posts
INSERT INTO posts (author_id, author_handle, content, likes_count, reposts_count, comments_count, created_at) VALUES
((SELECT id FROM users WHERE username = 'yourname'), 'yourname', 'Just shipped a new feature! The TUI is looking amazing 🚀', 12, 3, 2, NOW() - INTERVAL '5 minutes'),
((SELECT id FROM users WHERE username = 'alice'), 'alice', 'Working on a new CLI tool for developers. Any testers?', 45, 12, 1, NOW() - INTERVAL '15 minutes'),
((SELECT id FROM users WHERE username = 'bob'), 'bob', 'Refactoring is like cleaning your room. You know where everything is in the mess, but it''s still better to organize it.', 234, 67, 0, NOW() - INTERVAL '1 hour'),
((SELECT id FROM users WHERE username = 'techwriter'), 'techwriter', 'Just discovered this amazing TUI framework! #vim #tui #opensource', 234, 45, 18, NOW() - INTERVAL '2 hours'),
((SELECT id FROM users WHERE username = 'cliexpert'), 'cliexpert', 'Hot take: TUIs are making a comeback! 💻', 189, 52, 34, NOW() - INTERVAL '4 hours'),
((SELECT id FROM users WHERE username = 'vimfan'), 'vimfan', 'Finally got my vim config working with this social network.', 156, 28, 12, NOW() - INTERVAL '5 hours'),
((SELECT id FROM users WHERE username = 'charlie'), 'charlie', 'Building a new Rust-based terminal emulator. Excited to share progress!', 78, 15, 5, NOW() - INTERVAL '6 hours'),
((SELECT id FROM users WHERE username = 'opensource_dev'), 'opensource_dev', 'Just released v2.0 of my CLI tools library. Check it out!', 345, 89, 23, NOW() - INTERVAL '8 hours');

-- Insert some likes (post_interactions)
INSERT INTO post_interactions (post_id, user_id, interaction_type) VALUES
(1, (SELECT id FROM users WHERE username = 'yourname'), 'like'),
(1, (SELECT id FROM users WHERE username = 'alice'), 'like'),
(2, (SELECT id FROM users WHERE username = 'bob'), 'like');

-- Insert comments
INSERT INTO comments (post_id, user_id, username, text) VALUES
(1, (SELECT id FROM users WHERE username = 'alice'), 'alice', 'Looks awesome!'),
(1, (SELECT id FROM users WHERE username = 'bob'), 'bob', '🔥'),
(2, (SELECT id FROM users WHERE username = 'charlie'), 'charlie', 'Count me in');

-- Insert conversations (ensure participant_a_id < participant_b_id)
INSERT INTO conversations (participant_a_id, participant_b_id, last_message_preview, last_message_at) VALUES
(
    LEAST((SELECT id FROM users WHERE username = 'yourname'), (SELECT id FROM users WHERE username = 'alice')),
    GREATEST((SELECT id FROM users WHERE username = 'yourname'), (SELECT id FROM users WHERE username = 'alice')),
    'Thanks! Let me know if you need...',
    NOW() - INTERVAL '2 minutes'
),
(
    LEAST((SELECT id FROM users WHERE username = 'yourname'), (SELECT id FROM users WHERE username = 'charlie')),
    GREATEST((SELECT id FROM users WHERE username = 'yourname'), (SELECT id FROM users WHERE username = 'charlie')),
    'That sounds perfect!',
    NOW() - INTERVAL '1 hour'
),
(
    LEAST((SELECT id FROM users WHERE username = 'yourname'), (SELECT id FROM users WHERE username = 'bob')),
    GREATEST((SELECT id FROM users WHERE username = 'yourname'), (SELECT id FROM users WHERE username = 'bob')),
    'Working on a new CLI tool...',
    NOW() - INTERVAL '3 hours'
);

-- Insert messages for conversation between yourname and alice
INSERT INTO messages (conversation_id, sender_id, sender_handle, content, is_read, created_at) VALUES
(1, (SELECT id FROM users WHERE username = 'alice'), 'alice', 'Hey! Did you see the new feature I pushed?', TRUE, NOW() - INTERVAL '15 minutes'),
(1, (SELECT id FROM users WHERE username = 'yourname'), 'yourname', 'Yes! It looks amazing! 🎉', TRUE, NOW() - INTERVAL '13 minutes'),
(1, (SELECT id FROM users WHERE username = 'yourname'), 'yourname', 'The TUI design is so clean. How did you implement the navigation system?', TRUE, NOW() - INTERVAL '12 minutes'),
(1, (SELECT id FROM users WHERE username = 'alice'), 'alice', 'State machine for navigation. Want me to share code?', TRUE, NOW() - INTERVAL '8 minutes'),
(1, (SELECT id FROM users WHERE username = 'yourname'), 'yourname', 'That would be great! Happy to test too.', TRUE, NOW() - INTERVAL '30 seconds');

-- Insert notifications
INSERT INTO notifications (user_id, type, actor_id, actor_handle, content, post_id, read, created_at) VALUES
((SELECT id FROM users WHERE username = 'yourname'), 'mention', (SELECT id FROM users WHERE username = 'charlie'), 'charlie', '@yourname what do you think?', 4, FALSE, NOW() - INTERVAL '5 minutes'),
((SELECT id FROM users WHERE username = 'yourname'), 'like', (SELECT id FROM users WHERE username = 'alice'), 'alice', 'liked your post', 1, FALSE, NOW() - INTERVAL '15 minutes');

