interface SkeletonProps {
  className?: string;
  width?: string;
  height?: string;
}

export function Skeleton({ className = "", width, height }: SkeletonProps) {
  const style = {
    width: width || "100%",
    height: height || "1rem",
  };

  return <div className={`skeleton ${className}`} style={style} />;
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="skeleton-text">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={i === lines - 1 ? "60%" : "100%"}
          height="0.875rem"
        />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <Skeleton height="1.25rem" width="70%" />
      <SkeletonText lines={2} />
    </div>
  );
}

export function SkeletonNoteList({ count = 5 }: { count?: number }) {
  return (
    <div className="skeleton-note-list">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton-note-item">
          <Skeleton height="1.1rem" width="80%" />
          <Skeleton height="0.8rem" width="40%" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonEditor() {
  return (
    <div className="skeleton-editor">
      <div className="skeleton-editor-toolbar">
        <Skeleton height="2rem" width="100%" />
      </div>
      <div className="skeleton-editor-content">
        <Skeleton height="2rem" width="60%" />
        <SkeletonText lines={8} />
        <Skeleton height="1.5rem" width="50%" />
        <SkeletonText lines={5} />
      </div>
    </div>
  );
}

export function SkeletonGraph() {
  return (
    <div className="skeleton-graph">
      <div className="skeleton-graph-header">
        <Skeleton height="1.5rem" width="40%" />
      </div>
      <div className="skeleton-graph-content">
        <Skeleton height="100%" width="100%" />
      </div>
    </div>
  );
}
