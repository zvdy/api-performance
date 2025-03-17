-- Create demo tables for API performance testing

-- Authors table
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Posts table with foreign key to authors
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    author_id INTEGER REFERENCES authors(id),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    views INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Comments table with foreign key to posts
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    author_name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Post-Tags many-to-many relationship
CREATE TABLE post_tags (
    post_id INTEGER REFERENCES posts(id),
    tag_id INTEGER REFERENCES tags(id),
    PRIMARY KEY (post_id, tag_id)
);

-- Create indexes for performance
CREATE INDEX idx_posts_author_id ON posts(author_id);
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_post_tags_post_id ON post_tags(post_id);
CREATE INDEX idx_post_tags_tag_id ON post_tags(tag_id);

-- Insert sample data

-- Authors
INSERT INTO authors (name, email, bio) VALUES
('John Doe', 'john@example.com', 'Software engineer and blogger'),
('Jane Smith', 'jane@example.com', 'Data scientist and tech writer'),
('Michael Johnson', 'michael@example.com', 'Full-stack developer and open source contributor'),
('Sarah Williams', 'sarah@example.com', 'DevOps specialist and cloud architect'),
('Robert Brown', 'robert@example.com', 'Security expert and trainer');

-- Tags
INSERT INTO tags (name) VALUES
('programming'),
('python'),
('javascript'),
('database'),
('security'),
('web development'),
('api'),
('performance'),
('cloud'),
('docker');

-- Posts (20 sample posts)
INSERT INTO posts (author_id, title, content, published, views) VALUES
(1, 'Introduction to API Design', 'This post covers the basics of designing RESTful APIs...', TRUE, 1542),
(1, 'Python Best Practices', 'Learn about Python coding standards and best practices...', TRUE, 2103),
(2, 'Understanding Database Indexes', 'A deep dive into how database indexes work...', TRUE, 3250),
(2, 'Data Visualization Techniques', 'Various methods to visualize complex datasets...', TRUE, 1876),
(3, 'JavaScript Promises Explained', 'A comprehensive guide to JavaScript promises...', TRUE, 4215),
(3, 'Building Scalable APIs', 'Learn how to design APIs that scale effectively...', TRUE, 3089),
(4, 'Docker for Beginners', 'Getting started with containerization using Docker...', TRUE, 5302),
(4, 'CI/CD Pipeline Best Practices', 'Optimize your continuous integration workflows...', TRUE, 2648),
(5, 'Securing Your Web Applications', 'Essential security practices for web developers...', TRUE, 4720),
(5, 'Introduction to Cryptography', 'Understanding basic cryptographic concepts...', TRUE, 3104),
(1, 'Advanced Python Decorators', 'Deep dive into Python decorator patterns...', TRUE, 1865),
(2, 'SQL Query Optimization', 'Techniques to improve your database query performance...', TRUE, 2547),
(3, 'React Hooks in Depth', 'Understanding React hooks and their applications...', TRUE, 3651),
(4, 'Kubernetes Administration', 'Managing containerized applications at scale...', TRUE, 2973),
(5, 'OAuth 2.0 Implementation Guide', 'Step by step guide to implementing OAuth 2.0...', TRUE, 3214),
(1, 'Asynchronous Programming Patterns', 'Understanding async/await and other patterns...', FALSE, 0),
(2, 'Machine Learning for Developers', 'Introduction to ML concepts for programmers...', FALSE, 0),
(3, 'GraphQL vs REST', 'Comparing two popular API paradigms...', FALSE, 0),
(4, 'Infrastructure as Code', 'Managing your infrastructure using code...', FALSE, 0),
(5, 'Web Security Headers Explained', 'Understanding HTTP security headers...', FALSE, 0);

-- Comments (simulate more comments on popular posts)
-- Generate 200 sample comments
DO $$
DECLARE
    i INTEGER;
    post_count INTEGER := 15; -- Number of published posts
    comment_text TEXT[] := ARRAY[
        'Great article, very informative!',
        'Thanks for sharing this knowledge.',
        'I learned a lot from this post.',
        'Could you elaborate more on point 3?',
        'I disagree with some parts, but overall good content.',
        'This helped me solve a problem I was facing.',
        'Well written and easy to understand.',
        'I would like to see more examples.',
        'Looking forward to your next post!',
        'Have you considered talking about related topic X?'
    ];
    post_id INTEGER;
    author_names TEXT[] := ARRAY[
        'Alice', 'Bob', 'Charlie', 'Diana', 'Edward', 
        'Fiona', 'George', 'Hannah', 'Ivan', 'Julia',
        'Kevin', 'Laura', 'Mark', 'Nina', 'Oscar',
        'Patricia', 'Quincy', 'Rachel', 'Steve', 'Tina'
    ];
BEGIN
    FOR i IN 1..200 LOOP
        -- Assign comments more heavily to popular posts (lower IDs in our sample)
        IF i <= 80 THEN
            post_id := (i % 5) + 1; -- More comments on first 5 posts
        ELSIF i <= 150 THEN
            post_id := ((i % 5) + 6); -- Medium amount on next 5
        ELSE
            post_id := ((i % 5) + 11); -- Fewer on the last 5 published
        END IF;
        
        INSERT INTO comments (post_id, author_name, content)
        VALUES (
            post_id,
            author_names[(i % 20) + 1],
            comment_text[(i % 10) + 1]
        );
    END LOOP;
END $$;

-- Post-Tags relationships (assign multiple tags to each post)
DO $$
DECLARE
    i INTEGER;
    post_id INTEGER;
    tag_id INTEGER;
    tag_count INTEGER;
BEGIN
    FOR post_id IN 1..20 LOOP
        -- Assign 2-4 tags to each post
        tag_count := 2 + (post_id % 3); -- Results in 2, 3, or 4 tags
        
        FOR i IN 1..tag_count LOOP
            -- Choose a tag ID (ensure uniqueness per post)
            tag_id := ((post_id + i) % 10) + 1;
            
            -- Insert the post-tag relationship
            INSERT INTO post_tags (post_id, tag_id)
            VALUES (post_id, tag_id)
            ON CONFLICT DO NOTHING; -- Avoid duplicate entries
        END LOOP;
    END LOOP;
END $$; 