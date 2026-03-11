import { useState, useEffect } from 'react';
import Layout from './components/Layout';
import Tutorial from './components/Tutorial';
import { checkHealth } from './lib/api';

export default function App() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const check = async () => {
      try {
        const data = await checkHealth();
        setHealth(data);
      } catch {
        setHealth({ status: 'error', model: { healthy: false } });
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <Tutorial />
      <Layout health={health} />
    </>
  );
}
