import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import type { Control, FieldErrors, UseFormRegister } from 'react-hook-form';
import { useFieldArray, useForm } from 'react-hook-form';
import { useParams } from 'react-router-dom';
import { z } from 'zod';
import api from '../services/api';
import useAuthStore from '../store/authStore';


// Zod schema for collection fields
const collectionFieldSchema = z.object({
  name: z.string().min(1, 'Field name is required'),
  type: z.string().min(1, 'Field type is required'),
});

// Zod schema for creating a collection
const createCollectionSchema = z.object({
  collections: z.array(
    z.object({
      name: z.string().min(1, 'Collection name is required').regex(/^[a-zA-Z0-9_-]+$/, 'Collection name can only contain letters, numbers, underscores, and hyphens'),
      fields: z.array(collectionFieldSchema).min(1, 'At least one field is required'),
    })
  ).min(1, 'At least one collection is required'),
});

type CreateCollectionForm = z.infer<typeof createCollectionSchema>;

interface Collection {
  name: string;
  field_count: number;
  num_documents: number;
}

interface Database {
  database: {
    _id: string;
    user_id: string;
    displayName: string;
    dbName: string;
  };
  collections: Collection[];
  stats: {
    collection_count: number;
    total_fields: number;
  };
}

const DatabaseDetail = () => {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { token } = useAuthStore();
  const [isCreateCollectionModalOpen, setIsCreateCollectionModalOpen] = useState(false);

  // Fetch database details
  const { data, isLoading, error } = useQuery<Database>({
    queryKey: ['database', id],
    queryFn: async () => {
      const response = await api.get(`/core/api/v1/database/${id}`);
      return response;
    },
    enabled: !!token && !!id,
  });

  // Delete collection mutation
  const deleteMutation = useMutation({
    mutationFn: async ({ collection_name }: { collection_name: string }) => {
      if (!data) return;
      await api.delete('/api/drop_collections/', { database_id: id, collection_names: [collection_name] });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['database', id] }); // Invalidate specific database to refetch collections
      alert('Collection deleted successfully!');
    },
    onError: (err) => {
      console.error('Failed to delete collection:', err);
      alert('Failed to delete collection. Please try again.');
    },
  });

  const handleDelete = ({ collection_name }: { collection_name: string }) => {
    if (window.confirm(`Are you sure you want to delete "${collection_name}"? This action cannot be undone.`)) {
      deleteMutation.mutate({ collection_name });
    }
  };

  // Form setup for creating collections
  const { register, control, handleSubmit, reset, formState: { errors } } = useForm<CreateCollectionForm>({
    resolver: zodResolver(createCollectionSchema),
    defaultValues: { collections: [{ name: '', fields: [{ name: '', type: '' }] }] },
  });

  const { fields: collections, append: appendCollection, remove: removeCollection } = useFieldArray({
    control,
    name: 'collections',
  });

  // Create collections mutation
  const createCollectionsMutation = useMutation({
    mutationFn: async (formData: CreateCollectionForm) => {
      if (!id) throw new Error('Database ID is missing.');
      const payload = {
        database_id: id,
        collections: formData.collections.map(col => ({
          name: col.name,
          fields: col.fields.map(field => ({
            name: field.name,
            type: field.type,
          })),
        })),
      };
      const response = await api.post('/api/add_collection/', payload);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['database', id] });
      setIsCreateCollectionModalOpen(false);
      reset();
      alert('Collections created successfully!');
    },
    onError: (err) => {
      console.error('Failed to create collections:', err);
      alert('Failed to create collections. Please check your input and try again.');
    },
  });

  const onSubmitCreateCollections = (formData: CreateCollectionForm) => {
    createCollectionsMutation.mutate(formData);
  };


  return (
    <div className="bg-slate-900 text-slate-300 font-sans min-h-screen p-6 sm:p-10">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-white tracking-tight mb-8">
          {isLoading ? 'Loading Database...' : data?.database.displayName || 'Database Details'}
        </h1>
        <p className="mt-4 text-lg text-slate-400 mb-10">
          Overview of your database, including collections and their statistics.
        </p>

        {/* Database Stats */}
        <section className="p-6 bg-slate-800/50 rounded-xl border border-slate-700/80 mb-8">
          <h2 className="text-2xl font-semibold text-white tracking-tight mb-6">Database Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-700/40 p-5 rounded-lg border border-slate-600/50 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 text-emerald-400"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" /></svg>
                  Number of Collections
                </h3>
                <p className="text-3xl font-bold text-emerald-400">{data?.stats.collection_count ?? 0}</p>
              </div>
              <p className="text-xs text-slate-500 mt-3">Total collections in this database</p>
            </div>
            <div className="bg-slate-700/40 p-5 rounded-lg border border-slate-600/50 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 text-purple-400"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
                  Total Fields Across Collections
                </h3>
                <p className="text-3xl font-bold text-purple-400">{data?.stats.total_fields ?? 0}</p>
              </div>
              <p className="text-xs text-slate-500 mt-3">Sum of all fields defined in all collections</p>
            </div>
          </div>
        </section>

        {/* Collections Table */}
        <section className="p-6 bg-slate-800/50 rounded-xl border border-slate-700/80 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold text-white tracking-tight">Collections in "{data?.database.displayName || 'this database'}"</h2>
            <button
              onClick={() => setIsCreateCollectionModalOpen(true)}
              className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-4 py-2 rounded-md transition-colors duration-200 shadow-md"
              aria-label="Add new collection"
            >
              Add Collection
            </button>
          </div>
          {isLoading ? (
            <p className="text-slate-400">Loading collections...</p>
          ) : error ? (
            <p className="text-red-400">Error loading collections. Please try again later.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead>
                  <tr className="bg-slate-700/60">
                    <th className="p-3 text-left text-sm font-semibold text-slate-200 rounded-tl-lg">Collection Name</th>
                    <th className="p-3 text-left text-sm font-semibold text-slate-200">Fields Defined</th>
                    <th className="p-3 text-left text-sm font-semibold text-slate-200">Documents Stored</th>
                    <th className="p-3 text-left text-sm font-semibold text-slate-200 rounded-tr-lg">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.collections?.length ? (
                    data.collections.map((collection) => (
                      <tr key={collection.name} className="border-b border-slate-700/60 hover:bg-slate-700/40 transition-colors">
                        <td className="p-3 text-slate-300 font-medium">{collection.name}</td>
                        <td className="p-3 text-slate-400">{collection.field_count}</td>
                        <td className="p-3 text-slate-400">{collection.num_documents}</td>
                        <td className="p-3">
                          <button className="text-cyan-500 hover:text-cyan-400 font-medium transition-colors mr-4
                          disabled:opacity-50 disabled:cursor-not-allowed"
                            disabled={true} // Re-enable when view functionality is implemented
                          >
                            View
                          </button>
                          <button
                            onClick={() => handleDelete({ collection_name: collection.name })}
                            className="text-red-500 hover:text-red-400 font-medium transition-colors border-l border-slate-700/60 pl-4">
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="p-6 text-center text-slate-400 bg-slate-700/40 rounded-b-lg">
                        No collections found in this database.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Danger Zone (unchanged) */}
        <section className="p-6 bg-slate-800/50 rounded-xl border border-red-700/80 mb-8">
          <h2 className="text-2xl font-semibold text-red-400 tracking-tight mb-6">Danger Zone</h2>
          <div className="bg-red-900/20 p-5 rounded-lg border border-red-700/50">
            <p className="text-base text-red-300 mb-4">
              Delete this database. Once you delete a database, there is no going back. This action is irreversible and all data will be lost. Please be absolutely certain.
            </p>
            <button
              disabled={true} // Keep disabled as original example
              className="bg-red-600 hover:bg-red-700 text-white font-semibold px-6 py-2.5 rounded-md transition-colors duration-200 shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Delete database"
            >
              {'Delete Database'}
            </button>
          </div>
        </section>
      </div>

      {/* Create Collection Modal */}
      {isCreateCollectionModalOpen && (
        <div className="fixed inset-0 bg-opacity-70 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-slate-800/90 p-6 sm:p-8 rounded-xl max-w-2xl w-full mx-auto border border-cyan-700 shadow-2xl relative">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white tracking-tight">
                Add New Collection(s)
              </h2>
              <button
                onClick={() => setIsCreateCollectionModalOpen(false)}
                className="text-slate-400 hover:text-white transition-colors text-2xl"
                aria-label="Close form"
              >
                &times;
              </button>
            </div>
            <form onSubmit={handleSubmit(onSubmitCreateCollections)} className="space-y-6">
              <div>
                {errors.collections && (
                  <p className="text-red-400 text-sm mb-3">{errors.collections.message}</p>
                )}
                <div className="space-y-4">
                  {collections.map((collection, index) => (
                    <div key={collection.id} className="p-5 bg-slate-700/40 rounded-lg border border-slate-600/50 relative">
                      <label htmlFor={`collections.${index}.name`} className="block text-sm font-medium text-slate-300 mb-2">
                        Collection Name <span className="text-red-400">*</span>
                      </label>
                      <input
                        id={`collections.${index}.name`}
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
                        <CollectionFields
                          collectionIndex={index}
                          control={control}
                          register={register}
                          errors={errors}
                        />
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
                  onClick={() => setIsCreateCollectionModalOpen(false)}
                  className="bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white px-5 py-2.5 rounded-md text-sm font-medium transition-colors duration-200"
                  aria-label="Cancel"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createCollectionsMutation.isPending}
                  className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-2.5 px-6 rounded-md text-sm transition-colors duration-200 shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Create collections"
                >
                  {createCollectionsMutation.isPending ? 'Adding...' : 'Add Collection(s)'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatabaseDetail;

interface CollectionFieldsProps {
  collectionIndex: number;
  control: Control<CreateCollectionForm>;
  register: UseFormRegister<CreateCollectionForm>;
  errors: FieldErrors<CreateCollectionForm>;
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
      {typeof errors.collections?.[collectionIndex]?.fields?.message === 'string' && (
        <p className="text-red-400 text-sm mt-1">{errors.collections[collectionIndex].fields?.message}</p>
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
