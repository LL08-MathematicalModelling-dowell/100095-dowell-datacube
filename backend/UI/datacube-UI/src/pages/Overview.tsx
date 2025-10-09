/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '../services/api';
import useAuthStore from '../store/authStore';

// Define validation schema
const collectionFieldSchema = z.object({
  name: z.string().min(1, 'Field name is required'),
  type: z.string().min(1, 'Field type is required'),
});

const createDatabaseSchema = z.object({
  db_name: z.string().min(1, 'Database name is required').regex(/^[a-zA-Z0-9_-]+$/, 'Database name can only contain letters, numbers, underscores, and hyphens'),
  collections: z.array(
    z.object({
      name: z.string().min(1, 'Collection name is required'),
      fields: z.array(collectionFieldSchema).min(1, 'At least one field is required'),
    })
  ).min(1, 'At least one collection is required'),
});

type CreateDatabaseForm = z.infer<typeof createDatabaseSchema>;

interface Database {
  id: string;
  name: string;
}

const Overview = () => {
  const queryClient = useQueryClient();
  const { token } = useAuthStore();
  const [isFormOpen, setIsFormOpen] = useState(false);

  // Fetch databases and usage stats
  const { data: databases, isLoading, error } = useQuery<Database[]>({
    queryKey: ['databases'],
    queryFn: async () => {
      const response = await api.get('/core/api/v1/dashboard/stats/');
      return response.databases;
    },
    enabled: !!token,
  });

  // Create database mutation
  const createMutation = useMutation({
    mutationFn: (data: CreateDatabaseForm) => api.post('/api/create_database/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['databases'] });
      setIsFormOpen(false);
      reset();
      alert('Database created successfully!'); // Added success alert
    },
    onError: (err) => {
      console.error('Failed to create database:', err);
      alert('Failed to create database. Please check your input and try again.'); // More informative error
    },
  });

  // Form setup
  const { register, control, handleSubmit, reset, formState: { errors } } = useForm<CreateDatabaseForm>({
    resolver: zodResolver(createDatabaseSchema),
    defaultValues: { db_name: '', collections: [{ name: '', fields: [{ name: '', type: '' }] }] },
  });

  const { fields: collections, append: appendCollection, remove: removeCollection } = useFieldArray({
    control,
    name: 'collections',
  });

  const onSubmit = (data: CreateDatabaseForm) => {
    createMutation.mutate(data);
  };

  return (
    <div className="bg-slate-900 text-slate-300 font-sans min-h-screen p-6 sm:p-10">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-white tracking-tight mb-8">
          Dashboard Overview
        </h1>
        <p className="mt-4 text-lg text-slate-400 mb-10">
          A quick glance at your API usage and managed databases.
        </p>

        {/* API Usage Stats */}
        <section className="p-6 bg-slate-800/50 rounded-xl border border-slate-700/80 mb-8">
          <h2 className="text-2xl font-semibold text-white tracking-tight mb-6">
            API Usage & Statistics
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-slate-700/40 p-5 rounded-lg border border-slate-600/50 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 text-cyan-400"><path d="M4 14.899A7 7 0 0 1 15 12h3a5 5 0 0 1 0 10h-3.5" /><path d="M7 6l-3 3 3 3" /><path d="M10.5 9.5l3 3 3-3" /></svg>
                  API Calls This Month
                </h3>
                <p className="text-3xl font-bold text-cyan-400">0</p>
              </div>
              <p className="text-xs text-slate-500 mt-3">Next update in 24 hours</p>
            </div>
            <div className="bg-slate-700/40 p-5 rounded-lg border border-slate-600/50 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 text-emerald-400"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" /></svg>
                  Logical Databases
                </h3>
                <p className="text-3xl font-bold text-emerald-400">{databases?.length ?? 0}</p>
              </div>
              <p className="text-xs text-slate-500 mt-3">Total databases provisioned</p>
            </div>
            {/* You could add more stat cards here, e.g., Storage Used, Active Users, etc. */}
            <div className="bg-slate-700/40 p-5 rounded-lg border border-slate-600/50 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 text-purple-400"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
                  Active Endpoints
                </h3>
                <p className="text-3xl font-bold text-purple-400">0</p>
              </div>
              <p className="text-xs text-slate-500 mt-3">Endpoints connected to your databases</p>
            </div>
          </div>
        </section>

        {/* Databases List */}
        <section className="p-6 bg-slate-800/50 rounded-xl border border-slate-700/80 mb-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
            <h2 className="text-2xl font-semibold text-white tracking-tight">Your Databases</h2>
            <button
              onClick={() => setIsFormOpen(true)}
              className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-3 px-6 rounded-md transition-colors duration-200 shadow-md flex-shrink-0"
              aria-label="Create new database"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline-block mr-2"><path d="M12 5v14M5 12h14" /></svg>
              Create Database
            </button>
          </div>

          {isLoading && <p className="text-slate-400">Loading databases...</p>}
          {error && <p className="text-red-400">Error loading databases. Please try again later.</p>}

          {!isLoading && !error && databases && databases.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead>
                  <tr className="bg-slate-700/60">
                    <th className="p-3 text-left text-sm font-semibold text-slate-200 rounded-tl-lg">Database Name</th>
                    <th className="p-3 text-left text-sm font-semibold text-slate-200">Database ID</th>
                    <th className="p-3 text-left text-sm font-semibold text-slate-200 rounded-tr-lg">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {databases?.map((db) => (
                    <tr key={db.id} className="border-b border-slate-700/60 hover:bg-slate-700/40 transition-colors">
                      <td className="p-3 text-slate-300 font-medium">{db.name}</td>
                      <td className="p-3 font-mono text-sm text-slate-400">{db.id}</td>
                      <td className="p-3">
                        <Link
                          to={`/database/${db.id}`}
                          className="text-cyan-500 hover:text-cyan-400 font-medium transition-colors"
                        >
                          View Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (!isLoading && !error && databases?.length === 0) && (
            <div className="text-center p-6 bg-slate-700/40 rounded-lg border border-slate-600/50">
              <p className="text-slate-400 text-lg mb-4">You don't have any databases yet.</p>
              <button
                onClick={() => setIsFormOpen(true)}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-5 rounded-md transition-colors duration-200 shadow-md"
              >
                Start by creating one!
              </button>
            </div>
          )}
        </section>

        {/* Create Database Form Modal */}
        {isFormOpen && (
          <div className="fixed inset-0 bg-opacity-70 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-slate-800/90 p-6 sm:p-8 rounded-xl max-w-2xl w-full mx-auto border border-cyan-700 shadow-2xl relative">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white tracking-tight">
                  Create New Database
                </h2>
                <button
                  onClick={() => setIsFormOpen(false)}
                  className="text-slate-400 hover:text-white transition-colors text-2xl"
                  aria-label="Close form"
                >
                  &times;
                </button>
              </div>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div>
                  <label htmlFor="db_name" className="block text-sm font-medium text-slate-300 mb-2">
                    Database Name <span className="text-red-400">*</span>
                  </label>
                  <input
                    id="db_name"
                    {...register('db_name')}
                    placeholder="e.g., my_customer_project"
                    className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                    aria-invalid={errors.db_name ? 'true' : 'false'}
                  />
                  {errors.db_name && (
                    <p className="text-red-400 text-sm mt-1">{errors.db_name.message}</p>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-slate-200 mb-3 flex items-center">
                    Collections & Fields <span className="text-red-400 ml-1">*</span>
                  </h3>
                  {errors.collections && (
                    <p className="text-red-400 text-sm mb-3">{errors.collections.message}</p>
                  )}
                  <div className="space-y-4">
                    {collections.map((collection, index) => (
                      <div key={collection.id} className="p-5 bg-slate-700/40 rounded-lg border border-slate-600/50 relative">
                        <input
                          {...register(`collections.${index}.name`)}
                          placeholder="Collection Name (e.g., 'users')"
                          className="w-full p-2 bg-slate-600/50 border border-slate-500 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors mb-3"
                          aria-invalid={errors.collections?.[index]?.name ? 'true' : 'false'}
                        />
                        {errors.collections?.[index]?.name && (
                          <p className="text-red-400 text-sm mb-3">{errors.collections[index].name?.message}</p>
                        )}

                        <h4 className="text-sm font-medium text-slate-300 mb-2">Fields for "{collection.name || 'New Collection'}" <span className="text-red-400">*</span></h4>
                        {errors.collections?.[index]?.fields && (
                          <p className="text-red-400 text-sm mb-3">{errors.collections[index].fields?.message}</p>
                        )}

                        <div className="space-y-2">
                          <CollectionFields fields={collection.fields} collectionIndex={index} control={control} register={register} errors={errors} />
                        </div>

                        <button
                          type="button"
                          onClick={() => removeCollection(index)}
                          className="absolute top-3 right-3 text-slate-400 hover:text-red-500 transition-colors"
                          aria-label="Remove collection"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
                        </button>
                      </div>
                    ))}
                  </div>
                  {errors.collections && (
                    <p className="text-red-400 text-sm mt-3">{errors.collections.message}</p>
                  )}
                  <button
                    type="button"
                    onClick={() => appendCollection({ name: '', fields: [{ name: '', type: '' }] })}
                    className="mt-4 text-cyan-500 hover:text-cyan-400 font-medium transition-colors flex items-center gap-1"
                    aria-label="Add another collection"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14" /></svg>
                    Add Another Collection
                  </button>
                </div>

                <div className="flex justify-end gap-4 mt-8 pt-6 border-t border-slate-700/60">
                  <button
                    type="button"
                    onClick={() => setIsFormOpen(false)}
                    className="bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white px-5 py-2.5 rounded-md text-sm font-medium transition-colors duration-200"
                    aria-label="Cancel"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createMutation.isPending}
                    className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-2.5 px-6 rounded-md text-sm transition-colors duration-200 shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label="Create database"
                  >
                    {createMutation.isPending ? 'Creating...' : 'Create Database'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Overview;

// Helper component for Collection Fields to manage nested field array
interface CollectionFieldsProps {
  fields: any[]; // Use correct type if available, e.g., Array<z.infer<typeof collectionFieldSchema>>
  collectionIndex: number;
  control: any;
  register: any;
  errors: any;
}

const CollectionFields: React.FC<CollectionFieldsProps> = ({ collectionIndex, control, register, errors }) => {
  const { fields: fieldArrayFields, append: appendField, remove: removeField } = useFieldArray({
    control,
    name: `collections.${collectionIndex}.fields`,
  });

  return (
    <div className="space-y-2">
      {fieldArrayFields.map((field, fieldIndex) => (
        <div key={field.id} className="flex gap-2 items-center">
          <input
            {...register(`collections.${collectionIndex}.fields.${fieldIndex}.name`)}
            placeholder="Field Name"
            className="flex-grow p-2 bg-slate-600/50 border border-slate-500 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
            aria-invalid={errors.collections?.[collectionIndex]?.fields?.[fieldIndex]?.name ? 'true' : 'false'}
          />
          <input
            {...register(`collections.${collectionIndex}.fields.${fieldIndex}.type`)}
            placeholder="Field Type (e.g., 'string', 'number')"
            className="flex-grow p-2 bg-slate-600/50 border border-slate-500 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
            aria-invalid={errors.collections?.[collectionIndex]?.fields?.[fieldIndex]?.type ? 'true' : 'false'}
          />
          <button
            type="button"
            onClick={() => removeField(fieldIndex)}
            className="text-slate-400 hover:text-red-500 transition-colors p-1"
            aria-label="Remove field"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
          </button>
        </div>
      ))}
      {errors.collections?.[collectionIndex]?.fields?._errors && (
        <p className="text-red-400 text-sm mt-1">{errors.collections[collectionIndex].fields._errors.join(', ')}</p>
      )}
      <button
        type="button"
        onClick={() => appendField({ name: '', type: '' })}
        className="mt-2 text-emerald-500 hover:text-emerald-400 font-medium transition-colors flex items-center gap-1"
        aria-label="Add another field"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14" /></svg>
        Add Field
      </button>
    </div>
  );
};