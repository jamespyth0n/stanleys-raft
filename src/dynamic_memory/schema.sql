PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS atoms (
    atom_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS atom_versions (
    version_id TEXT PRIMARY KEY,
    atom_id TEXT NOT NULL,
    version_no INTEGER NOT NULL CHECK (version_no >= 1),

    content TEXT NOT NULL,
    content_hash TEXT NOT NULL
        CHECK (
            length(content_hash) = 64
            AND content_hash NOT GLOB '*[^0-9a-f]*'
        ),

    knowledge_type TEXT NOT NULL CHECK (
        knowledge_type IN (
            'fact', 'observation', 'preference',
            'concept', 'question', 'intention',
            'procedure', 'hypothesis', 'conclusion'
        )
    ),

    epistemic_status TEXT NOT NULL CHECK (
        epistemic_status IN (
            'asserted', 'observed', 'inferred',
            'hypothesized', 'concluded'
        )
    ),

    verification_status TEXT NOT NULL CHECK (
        verification_status IN (
            'unverified', 'verified', 'challenged'
        )
    ),

    valid_from TEXT,
    valid_until TEXT,

    created_at TEXT NOT NULL,
    supersedes_version_id TEXT,

    UNIQUE (atom_id, version_no),
    UNIQUE (atom_id, version_id),

    FOREIGN KEY (atom_id)
        REFERENCES atoms(atom_id),

    FOREIGN KEY (atom_id, supersedes_version_id)
        REFERENCES atom_versions(atom_id, version_id),

    CHECK (
        supersedes_version_id IS NULL
        OR supersedes_version_id <> version_id
    ),

    -- IMPLEMENTATION PATCH B03-P01:
    -- Corrects the ineffective temporal CHECK in the ratified package.
    -- When both dates exist, valid_until must not precede valid_from.
    CHECK (
        valid_from IS NULL
        OR valid_until IS NULL
        OR valid_until >= valid_from
    )
);

CREATE TABLE IF NOT EXISTS provenance (
    provenance_id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL,

    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_locator TEXT,

    source_created_at TEXT,
    captured_at TEXT NOT NULL,
    source_content_hash TEXT,

    FOREIGN KEY (version_id)
        REFERENCES atom_versions(version_id)
);

CREATE INDEX IF NOT EXISTS idx_atom_versions_atom
    ON atom_versions(atom_id, version_no);

CREATE INDEX IF NOT EXISTS idx_provenance_version
    ON provenance(version_id);

CREATE TABLE IF NOT EXISTS atom_version_relations (
    relation_id TEXT PRIMARY KEY,

    from_version_id TEXT NOT NULL,
    to_version_id TEXT NOT NULL,

    relation_type TEXT NOT NULL CHECK (
        relation_type IN ('disputes')
    ),

    created_at TEXT NOT NULL,

    FOREIGN KEY (from_version_id)
        REFERENCES atom_versions(version_id),

    FOREIGN KEY (to_version_id)
        REFERENCES atom_versions(version_id),

    CHECK (from_version_id <> to_version_id)
);

CREATE INDEX IF NOT EXISTS idx_relations_from
    ON atom_version_relations(from_version_id);

CREATE INDEX IF NOT EXISTS idx_relations_to
    ON atom_version_relations(to_version_id);

CREATE TABLE IF NOT EXISTS activity_events (
    event_id TEXT PRIMARY KEY,

    event_type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,

    atom_id TEXT,
    version_id TEXT,

    details_json TEXT,

    FOREIGN KEY (atom_id, version_id)
        REFERENCES atom_versions(atom_id, version_id),

    CHECK (
        (atom_id IS NULL AND version_id IS NULL)
        OR
        (atom_id IS NOT NULL AND version_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_activity_occurred
    ON activity_events(occurred_at);

CREATE INDEX IF NOT EXISTS idx_activity_atom
    ON activity_events(atom_id, version_id);

CREATE TRIGGER IF NOT EXISTS prevent_atom_version_update
BEFORE UPDATE ON atom_versions
BEGIN
    SELECT RAISE(ABORT, 'Atom versions are immutable');
END;

CREATE TRIGGER IF NOT EXISTS prevent_atom_version_delete
BEFORE DELETE ON atom_versions
BEGIN
    SELECT RAISE(ABORT, 'Atom versions are immutable');
END;