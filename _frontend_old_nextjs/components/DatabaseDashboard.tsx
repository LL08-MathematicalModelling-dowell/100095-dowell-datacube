// components/DatabaseDashboard.tsx
import Link from 'next/link';
import React from 'react';
import {
  FaPlus,
  FaDatabase,
  FaTable,
  FaListUl,
  FaInfoCircle,
} from 'react-icons/fa';
import { Spinner } from '@chakra-ui/react';

interface Database {
  id: string;
  name: string;
  numCollections: number;
  description: string;
  createdAt: string;
}

interface DatabaseDashboardProps {
  databases: Database[];
  onCreateDatabase: () => void;
  isLoading: boolean;
  fetchNextPage: () => void;
  hasNextPage: boolean;
  status: 'pending' | 'error' | 'success';
}

const DatabaseDashboard: React.FC<DatabaseDashboardProps> = ({
  databases,
  onCreateDatabase,
  isLoading,
  fetchNextPage,
  hasNextPage,
  status,
}) => {
  return (
    <div className="bg-gray-900 min-h-screen p-6">
      <h1 className="text-3xl font-bold text-white mb-6 flex items-center">
        <FaDatabase className="mr-2 text-orange-500" /> Database Management
      </h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
        {!isLoading && databases.length === 0 && (
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg text-center text-white col-span-full">
            <p className="text-xl font-semibold">No Databases Found</p>
            <p className="text-gray-400 mt-2">
              You haven’t created any databases yet. Use the “Create Database”
              button below to get started.
            </p>
          </div>
        )}

        {databases.map((db) => (
          <Link
            key={db.id}
            href={`/dashboard/databases/${db.id}`}
            className="block"
          >
            <div className="bg-gray-800 p-5 rounded-lg shadow-lg hover:shadow-xl transition cursor-pointer flex flex-col justify-between h-full">
              <div>
                <h2 className="text-xl font-semibold text-white flex items-center truncate">
                  <FaTable className="mr-2 text-blue-400" /> {db.name}
                </h2>
                <p className="text-gray-300 flex items-center mt-2">
                  <FaListUl className="mr-1 text-yellow-400" />
                  {db.numCollections} collections
                </p>
                <p className="text-gray-400 mt-1 flex items-center">
                  <FaInfoCircle className="mr-1 text-green-400" />
                  {db.description || 'No description'}
                </p>
              </div>
              <p className="text-gray-500 text-sm mt-4">
                Created{' '}
                {new Date(db.createdAt).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })}
              </p>
            </div>
          </Link>
        ))}

        {/* Create new database card */}
        <div
          onClick={onCreateDatabase}
          className="bg-gray-700 flex items-center justify-center h-40 rounded-lg hover:bg-gray-600 transition cursor-pointer"
        >
          <div className="text-white text-xl flex items-center">
            <FaPlus className="mr-2 text-green-400" /> Create Database
          </div>
        </div>
      </div>

      {hasNextPage && (
        <div className="mt-8 flex justify-center">
          <button
            onClick={fetchNextPage}
            disabled={status === 'pending'}
            className="flex items-center bg-blue-600 hover:bg-blue-500 text-white py-2 px-4 rounded shadow-md transition focus:outline-none"
          >
            {status === 'pending' ? (
              <>
                <Spinner color="white" size="sm" className="mr-2" /> Loading…
              </>
            ) : (
              <>
                <FaPlus className="mr-2" /> Load More
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default DatabaseDashboard;

